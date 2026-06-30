# Import packages
import os
import sys
import time
import shutil
import argparse
import traceback
from logs.log import Log
from logs.console import warn
from params.parameters_factory import ParametersFactory
from details.details_manager import DetailsManager
from environments.env_factory import EnvFactory
from evals.eval_factory import EvalFactory
from models.cost_calculator import CostCalculator
from models.model_factory import ModelFactory
from agents.agent_factory import AgentFactory
from renderers.renderer_factory import RendererFactory
from states.env_state import EnvState
from states.global_state import GlobalState
from states.step_state import StepState
from states.agent_state import AgentState
from memory.memory_manager import MemoryManager
from results.results_manager import ResultsManager
from messages.messages_writer import MessagesWriter
from states.writer.state_writer import StateWriter

# Set parameters
steps_floor = 20
steps_ceiling = 100
sleep_time = 1
use_azure = False


def run_episode(split_name, model_name, agent_name, env_name, eval_name, episode_id, force=False):

    # Create the parameters
    parameters_factory = ParametersFactory()
    params = parameters_factory.create(
        split_name=split_name,
        model_name=model_name,
        agent_name=agent_name,
        env_name=env_name,
        eval_name=eval_name,
        episode_id=episode_id)

    # Echo the resolved config
    print(f"--- Running {params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} - episode-{episode_id} ---")

    # Skip if the episode already ran
    results_manager = ResultsManager()
    if not force and results_manager.exists(params):
        warn(f"Episode {episode_id} already exists. Skipping (use --force to re-run).")
        return 0

    # Remove the prior episode folder when forcing a re-run
    folder_path = f"../data/artifacts/{params.split_name}/{params.model_name}/{params.agent_name}/{params.eval_name}/episode-{episode_id}"
    if force and os.path.exists(folder_path):
        shutil.rmtree(folder_path)

    # Create components
    model_factory = ModelFactory()
    agent_factory = AgentFactory()
    eval_factory = EvalFactory()
    env_factory = EnvFactory()
    cost_calculator = CostCalculator()
    agent_writer = MessagesWriter()
    state_writer = StateWriter()

    # Create entities
    eval = eval_factory.create(params)
    env = env_factory.create(params, eval)

    # Create the log
    renderer = RendererFactory.create()
    log = Log(renderer, params)
    log.head(f"--- Starting {params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} - episode-{episode_id} ---")

    # Create the episode
    episode = eval.iloc[episode_id - 1].to_dict()
    solution_steps = episode["solution_steps"]
    max_steps = int(solution_steps * 1.5)
    max_steps = max(steps_floor, min(steps_ceiling, max_steps))
    params.max_steps = max_steps

    # Create entities
    model = model_factory.create(params, use_azure)
    react_k0 = agent_factory.create("react-k0", params, model)
    react_k1 = agent_factory.create("react-k1", params, model)
    react_kn = agent_factory.create("react-kn", params, model)
    summarizer = agent_factory.create("summarizer", params, model)
    planner = agent_factory.create("planner", params, model)
    memorizer = agent_factory.create("memorizer", params, model)
    reasoner = agent_factory.create("reasoner", params, model)
    actor = agent_factory.create("actor", params, model)
    memory_manager = MemoryManager()
    details_manager = DetailsManager(params)

    # Reset the variables
    global_state = GlobalState()
    action = ""
    final_reward = 0.0
    final_score = 0
    step_id = 0
    is_success = False
    errored = False

    # Create result row
    result_row = results_manager.create(params)
    result_row.episode = params.episode_id
    result_row.start_time = time.time()

    try:

        # Reset the model/agents
        model.reset()
        react_k0.reset()
        react_k1.reset()
        react_kn.reset()
        summarizer.reset()
        planner.reset()
        memorizer.reset()
        reasoner.reset()
        actor.reset()

        # Run the agent in the environment
        for step_id in range(params.max_steps + 1):

            # Set up the model
            model.reset_step()

            # Set up the state
            agent_state = AgentState()
            step_state = StepState(
                agent_state=agent_state,
                env_state=EnvState())
            step_state.step_id = step_id + 1
            step_state.agent_state = agent_state
            global_state.step_history.append(step_state)

            # Get the environment's state
            if step_id == 0:
                task_state, env_state = env.reset(episode_id)
                log.info(f"Task: {task_state.task}")
                global_state.task_state = task_state
                result_row.task = task_state.task
            else:
                env_state = env.step(action)

            # Set the state
            global_state.task_state.step_id = step_id + 1
            step_state.env_state = env_state

            # If max steps reached, end the episode
            if step_id == params.max_steps and not env_state.is_done:
                result_row.max_steps_hit = True
                env_state.is_done = True

            # Handle the end of episode
            if env_state.is_done:
                final_score = env_state.score
                final_reward = env_state.reward
                is_success = final_reward == 1.0
                global_state.task_state.success = is_success
                break

            # Log the step
            log.step(step_state, global_state.task_state)

            # Log the history
            if params.use_summarizer:
                log.history(global_state.step_history[:-1])

            # Log the memories
            if params.use_memorizer:
                log.memories(global_state.memories)

            # Log the plan
            if params.use_planner:
                log.plan(global_state.plan)

            # Log the environment state
            log.env(env_state, global_state.task_state)

            # Log the agent state
            log.info(f"Agent:")

            # Use the ReAct-k0 agent
            if params.use_react_k0:
                thought, action = react_k0.execute(global_state)
                agent_writer.write(params, step_id + 1, "react_k0", react_k0.messages)
                agent_state.thought = thought
                agent_state.action = action
                log.info(f"  Thought: {thought}")
                log.info(f"  Action: {action}")

            # Use the ReAct-k1 agent
            if params.use_react_k1:
                thought, action = react_k1.execute(global_state)
                agent_writer.write(params, step_id + 1, "react_k1", react_k1.messages)
                agent_state.thought = thought
                agent_state.action = action
                log.info(f"  Thought: {thought}")
                log.info(f"  Action: {action}")

            # Use the ReAct-kn agent
            if params.use_react_kn:
                thought, action = react_kn.execute(global_state)
                agent_writer.write(params, step_id + 1, "react", react_kn.messages)
                agent_state.thought = thought
                agent_state.action = action
                log.info(f"  Thought: {thought}")
                log.info(f"  Action: {action}")

            # Get the summarizer's summary
            if params.use_summarizer:
                summary = summarizer.execute(global_state)
                agent_writer.write(params, step_id + 1, "summarizer", summarizer.messages)
                agent_state.summary = summary
                log.info(f"  Summary: {summary}")

            # Get the memorizer's memory updates
            if params.use_memorizer:
                memory_updates = memorizer.execute(global_state)
                agent_writer.write(params, step_id + 1, "memorizer", memorizer.messages)
                global_state.memories = memory_manager.execute(global_state.memories, memory_updates)
                agent_state.memory = memory_updates
                memory_updates = renderer.render_memory_updates(memory_updates)
                log.info(f"  Memory:\n{memory_updates}")

            # Get the planner's plan
            if params.use_planner:
                new_plan = planner.execute(global_state)
                agent_writer.write(params, step_id + 1, "planner", planner.messages)
                if new_plan.strip() != "NO_CHANGE":
                    global_state.plan = new_plan
                    agent_state.plan = new_plan
                else:
                    agent_state.plan = global_state.plan
                new_plan = renderer.render_plan_updates(new_plan)
                log.info(f"  Plan:\n{new_plan}")

            # Get the reasoner's thought
            if params.use_reasoner:
                thought = reasoner.execute(global_state)
                agent_writer.write(params, step_id + 1, "reasoner", reasoner.messages)
                agent_state.thought = thought
                log.info(f"  Thought: {thought}")

            # Get the agent's action
            if params.use_actor:
                action = actor.execute(global_state)
                agent_writer.write(params, step_id + 1, "actor", actor.messages)
                agent_state.action = action
                log.info(f"  Action: {action}")

            # Truncate the action (if it's too long)
            if len(action) > 128:
                action = action[:128] + "... [Warning: Action truncated due to length. Use a shorter action.]"

            # Create details row
            details_row = details_manager.create()
            details_row.step_id = step_id + 1
            details_row.feedback = env_state.feedback
            details_row.location = env_state.location
            details_row.description = env_state.description
            details_row.inventory = env_state.inventory
            details_row.score = env_state.score
            details_row.reward = env_state.reward
            details_row.is_done = env_state.is_done
            details_row.summary = agent_state.summary
            details_row.thought = agent_state.thought
            details_row.action = agent_state.action
            details_row.cached_tokens = model.step_cached_tokens
            details_row.input_tokens = model.step_input_tokens
            details_row.reasoning_tokens = model.step_reasoning_tokens
            details_row.output_tokens = model.step_output_tokens
            details_row.total_tokens = model.step_total_tokens
            details_manager.add(details_row)

            # Sleep for n seconds to avoid API throttling
            time.sleep(sleep_time)
            log.info("")

    except Exception as e:
        errored = True
        error_message = f"{type(e).__name__}: {e}\n" \
            + traceback.format_exc()
        result_row.error = error_message
        log.error(error_message)

    # Log the results
    log.info(f"Reward: {final_reward}")
    log.info(f"Success: {final_reward == 1.0}")
    log.head("--- End of task ---\n")
    log.close()

    # Update result row
    result_row.end_time = time.time()
    result_row.sleep_time = (sleep_time * (step_id + 1)) + model.wait_time
    result_row.total_time = result_row.end_time - result_row.start_time - result_row.sleep_time
    result_row.success = is_success
    result_row.reward = final_reward
    result_row.score = final_score
    result_row.max_score = global_state.task_state.max_score
    result_row.steps = len(details_manager.get_table())
    result_row.max_steps = params.max_steps
    result_row.solution_steps = episode["solution_steps"]
    result_row.model_version = model.model_version
    result_row.cached_tokens = model.cached_tokens
    result_row.input_tokens = model.input_tokens
    result_row.reasoning_tokens = model.reasoning_tokens
    result_row.output_tokens = model.output_tokens
    result_row.total_tokens = model.total_tokens
    result_row.input_cost = cost_calculator.get_input_cost(params.model_name, model.cached_tokens, model.input_tokens)
    result_row.output_cost = cost_calculator.get_output_cost(params.model_name, model.reasoning_tokens, model.output_tokens)
    result_row.total_cost = result_row.input_cost + result_row.output_cost
    result_row.reward_per_step = (final_reward / result_row.steps) if result_row.steps > 0 else 0.0
    result_row.reward_per_token = (final_reward / model.total_tokens) if model.total_tokens > 0 else 0.0
    results_manager.save_row(params, result_row)

    # Save the details
    details_manager.save()

    # Write the state
    state_writer.write(global_state, params)

    # Display the episode summary
    print(f"--- Summary for {params.split_name} - {params.model_name} - {params.agent_name} - {params.eval_name} - episode-{episode_id} ---")
    print(f"Success: {result_row.success}")
    print(f"Reward: {result_row.reward:.2f}")
    print(f"Score: {result_row.score}/{result_row.max_score}")
    print(f"Steps: {result_row.steps}")
    print(f"Total Tokens: {result_row.total_tokens}")
    print(f"Total Cost: ${result_row.total_cost:.2f}")
    print(f"Total Time: {result_row.total_time:.2f} seconds")
    print(f"Reward per Step: {result_row.reward_per_step:.4f}")
    print(f"Reward per Token: {result_row.reward_per_token:.6f}")
    print(f"Error: {result_row.error}")
    print("--- END OF EPISODE ---")
    print("")

    return 1 if errored else 0


def build_parser():
    parser = argparse.ArgumentParser(description="Run a single eval episode.")
    parser.add_argument("--split", default="train")
    parser.add_argument("--model", default="gpt-5.4")
    parser.add_argument("--agent", default="modular-full")
    parser.add_argument("--eval", default="tw-simple-1")
    parser.add_argument("--env", default="textworld")
    parser.add_argument("--episode", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    exit_code = run_episode(
        split_name=args.split,
        model_name=args.model,
        agent_name=args.agent,
        env_name=args.env,
        eval_name=args.eval,
        episode_id=args.episode,
        force=args.force)
    sys.exit(exit_code)
