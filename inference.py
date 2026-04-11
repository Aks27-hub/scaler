import json
import os
import re
import shutil
import subprocess
from openai import OpenAI
from traffic_env import TrafficEnv
from easy_task import EasyTask, grade_easy
from medium_task import MediumTask, grade_medium
from hard_task import HardTask, grade_hard


def _to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _normalize_base_url(raw_url):
    """Accept either /v1 or /v1/chat/completions and normalize to /v1."""
    url = (raw_url or "").strip().rstrip("/")
    if not url:
        return ""
    suffix = "/chat/completions"
    if url.endswith(suffix):
        url = url[: -len(suffix)]
    if not url.endswith("/v1"):
        url = f"{url}/v1"
    return url


def _fallback_action(state):
    if state.get("emergency_present"):
        return 2
    if max(state["cars_per_lane"]) > 5:
        return 1
    return 0


def _choose_action_with_ollama(state, model_name):
    prompt = (
        f"Current traffic state: {json.dumps(state)}\n"
        "Choose action (0: hold, 1: switch, 2: emergency override). Return a single integer."
    )
    try:
        completed = subprocess.run(
            ["ollama", "run", model_name, prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if e.stderr else ""
        raise RuntimeError(f"Ollama failed: {stderr or e}") from e

    reply = completed.stdout.strip()
    print(f"   [OLLAMA Output] '{reply}'")

    patterns = [
        r"\b(?:action|return value|I would choose action|choose action)\s*[:\-]?\s*([012])\b",
        r"\*\*([012])\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, reply, re.IGNORECASE)
        if match:
            return int(match.group(1))

    digits = re.findall(r"[012]", reply)
    if digits:
        return int(digits[-1])
    return 0


def _choose_action_with_llm(state, client, model_name):
    prompt = (
        f"Current traffic state: {json.dumps(state)}\n"
        "Choose action (0: hold, 1: switch, 2: emergency override). Return a single integer."
    )
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "You are a traffic light controller. You must reply strictly with ONLY a single digit: 0, 1, or 2. Do not include any words, reasoning, or punctuation.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=5,
        temperature=0.0,
    )
    reply = (response.choices[0].message.content or "").strip()
    print(f"   [LLM Output] '{reply}'")

    for char in reply:
        if char in "012":
            return int(char)
    return 0


def _choose_action(state, client, model_name, use_ollama=False):
    if use_ollama:
        return _choose_action_with_ollama(state, model_name)
    return _choose_action_with_llm(state, client, model_name)


def run_task(task_name, TaskClass, grader, client, model_name, use_llm=True, use_ollama=False, max_api_failures=3):
    task = TaskClass()
    config = task.get_config()
    config["id"] = task_name 
    env = TrafficEnv(config)
    state = env.reset()
    
    print(f"[START]\ntask={task_name} seed={config['random_seed']}")
    
    trajectory = []
    done = False
    api_failures = 0
    llm_enabled = bool(use_llm and (use_ollama or client is not None))
    
    while not done:
        action = _fallback_action(state)
        if llm_enabled:
            try:
                action = _choose_action(state, client, model_name, use_ollama=use_ollama)
                api_failures = 0
            except Exception as e:
                api_failures += 1
                source = "Ollama" if use_ollama else "LLM API"
                print(f"   [{source} ERROR / FALLBACK TRIGGERED] {str(e)}")
                print(f"   [FALLBACK POLICY] Using heuristic action={action}")
                if api_failures >= max_api_failures:
                    llm_enabled = False
                    print("   [LLM DISABLED] Too many consecutive failures; continuing with local policy.")
            
        next_state, reward, done, info = env.step(action)
        cleared = info.get("total_cars_cleared", 0)
        arrived = info.get("total_cars_arrived", 1)
        print(f"[STEP] step={env.steps} action={action} reward={round(reward, 4)} queue={state['cars_per_lane']} cleared={cleared}/{arrived} done={done}")
        
        trajectory.append({
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done,
            "info": info
        })
        state = next_state
        
    score = grader(trajectory)
    print(f"[END]\ntask={task_name} score={score}")

def main():
    api_base_url = _normalize_base_url(os.environ.get("API_BASE_URL", "https://router.huggingface.co/v1"))
    hf_token = os.environ.get("HF_TOKEN")
    model_name = os.environ.get("MODEL_NAME", "meta-llama/Llama-3-8b-chat-hf")
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama3:latest")
    use_llm = _to_bool(os.environ.get("USE_LLM", "true"), default=True)
    use_ollama = _to_bool(os.environ.get("USE_OLLAMA", "false"), default=False)
    max_api_failures = int(os.environ.get("MAX_API_FAILURES", "3"))

    client = None
    if use_ollama:
        if shutil.which("ollama") is None:
            print("[CONFIG] Ollama CLI not found in PATH; disabling Ollama and using local fallback policy.")
            use_ollama = False
        else:
            model_name = ollama_model
            print(f"[CONFIG] Using Ollama model: {model_name}")
    if use_ollama:
        # no external client required for Ollama
        pass
    elif use_llm:
        if not hf_token:
            print("[CONFIG] HF_TOKEN not set, disabling LLM API calls and using local fallback policy.")
            use_llm = False
        else:
            client = OpenAI(base_url=api_base_url, api_key=hf_token)
            print(f"[CONFIG] Using HF API model: {model_name}")
    else:
        print("[CONFIG] No LLM backend configured, using local fallback policy.")

    run_task(
        "easy",
        EasyTask,
        grade_easy,
        client,
        model_name,
        use_llm=use_llm,
        use_ollama=use_ollama,
        max_api_failures=max_api_failures,
    )
    run_task(
        "medium",
        MediumTask,
        grade_medium,
        client,
        model_name,
        use_llm=use_llm,
        use_ollama=use_ollama,
        max_api_failures=max_api_failures,
    )
    run_task(
        "hard",
        HardTask,
        grade_hard,
        client,
        model_name,
        use_llm=use_llm,
        use_ollama=use_ollama,
        max_api_failures=max_api_failures,
    )

if __name__ == "__main__":
    main()
