# Import packages
import time
import traceback
from common.log import Log
from common.console import warn
from common.parameters_factory import ParametersFactory
from details.details_manager import DetailsManager
from environments.env_factory import EnvFactory
from evals.eval_factory import EvalFactory
from models.cost_calculator import CostCalculator
from models.model_factory import ModelFactory
from agents.agent_factory import AgentFactory
from states.env_state import EnvState
from states.global_state import GlobalState
from states.step_state import StepState
from states.agent_state import AgentState
from results.results_manager import ResultsManager
from summaries.summary_manager import SummaryManager
from messages.messages_writer import MessagesWriter
from states.writer.state_writer import StateWriter
from reviews.review_writer import ReviewWriter
from agents.reviewer.reviewer import Reviewer
from typing import cast

# Set agents
agent_names = [
    # "baseline",
    # "plus-tasker",
    # "plus-reasoner",
    # "minus-tasker",
    # "minus-reasoner",
    "topline"
]

# Set models
model_names = [
    # "gpt-4.1-mini",
    "gpt-5.2"
]

# Set evals
eval_size = 1
eval_env_names = [
    # ("tw-simple-1", "textworld"),
    # ("tw-treasure-1", "textworld"),
    # ("tw-treasure-2", "textworld"),
    # ("tw-treasure-3", "textworld"),
    # ("tw-coin-1", "textworld"),
    # ("tw-coin-2", "textworld"),
    # ("tw-coin-3", "textworld"),
    # ("tw-cooking-1", "textworld"),
    # ("tw-cooking-2", "textworld"),
    ("tw-cooking-3", "textworld"),
]

# Set parameters
steps_floor = 20
steps_ceiling = 100
sleep_time = 1

# Create the runs
runs = []
parameters_factory = ParametersFactory()
for agent_name in agent_names:
    for model_name in model_names:
        for eval_env_name in eval_env_names:
            eval_name, env_name = eval_env_name
            params = parameters_factory.create(
                agent_name = agent_name,
                model_name = model_name,
                env_name = env_name,
                eval_name = eval_name,
                eval_size = eval_size)
            runs.append(params)

# Create components
model_factory = ModelFactory()
agent_factory = AgentFactory()
eval_factory = EvalFactory()
env_factory = EnvFactory()
cost_calculator = CostCalculator()
agent_writer = MessagesWriter()
state_writer = StateWriter()
review_writer = ReviewWriter()

for params in runs:
    print(f"--- Running {params.agent_name} - {params.model_name} - {params.eval_name} ---")

    # Create components
    results_manager = ResultsManager()
    summary_manager = SummaryManager()

    # Create entities
    eval = eval_factory.create(params)
    env = env_factory.create(params, eval)

    # Get the episodes to run
    num_episodes = min(len(eval), eval_size)
    episode_ids = list(range(1, num_episodes + 1))
    if num_episodes == 10:
        episode_ids = list(range(10, 101, 10))

    # Set up summaries
    if summary_manager.exists(params):
        warn(f"Summary for {params.agent_name} - {params.model_name} - {params.eval_name} already exists.")
        input("Press Enter to continue...")

    for episode_id in episode_ids:

        # Create the log
        log = Log(params, episode_id)
        log.head(f"--- Starting {params.agent_name} - {params.model_name} - {params.eval_name} - episode {episode_id} / {num_episodes} ---")
        
        # Create the episode
        episode = eval.iloc[episode_id - 1].to_dict()
        solution_steps = episode["solution_steps"]
        max_steps = int(solution_steps * 1.5)
        max_steps = max(steps_floor, min(steps_ceiling, max_steps))
        params.max_steps = max_steps
        
        # Create entities
        model = model_factory.create(params)
        tasker = agent_factory.create("tasker", params, model)
        reasoner = agent_factory.create("reasoner", params, model)
        actor = agent_factory.create("actor", params, model)
        reviewer_model = model_factory.create(params)
        reviewer = agent_factory.create("reviewer", params, reviewer_model)
        reviewer = cast(Reviewer, reviewer)
        details_manager = DetailsManager(params, episode_id)
        
        # Reset the variables
        global_state = GlobalState()
        action = ""
        answer = ""
        final_reward = 0.0
        step_id = 0
        is_done = False

        # Create result row
        result_row = results_manager.create(params)
        result_row.episode = episode_id
        result_row.start_time = time.time()

        try:

            # Reset the agents
            reasoner.reset()
            actor.reset()

            # Run the agent in the environment
            for step_id in range(params.max_steps):

                log.info(f"# Step {step_id + 1}")

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

                    # Get the revised task
                    if params.use_tasker:
                        task = tasker.execute(global_state)
                        agent_writer.write(params, episode_id, step_id + 1, "tasker", tasker.messages)
                        log.info(f"Revised task: {task}")
                        global_state.task_state.task = task
                        result_row.revised_task = task
                else:
                    env_state = env.step(action)

                # Set the state
                global_state.task_state.step_id = step_id + 1
                step_state.env_state = env_state

                # Log the environment state
                log.info(f"Environment:")
                log.info(f"  Feedback: {env_state.feedback}")
                log.info(f"  Location: {env_state.location}")
                log.info(f"  Description: {env_state.description}")
                log.info(f"  Inventory: {env_state.inventory}")
                log.info(f"  Capacity: {env_state.items} of {global_state.task_state.max_items}")
                log.info(f"  Score: {env_state.score} of {global_state.task_state.max_score}")
                log.info(f"  Done: {env_state.is_done}")

                # Log the agent state
                log.info(f"Agent:")

                # Get the reasoner's thought
                if params.use_reasoner:
                    thought = reasoner.execute(global_state)
                    agent_writer.write(params, episode_id, step_id + 1, "reasoner", reasoner.messages)
                    agent_state.thought = thought
                    log.info(f"  Thought: {thought}")

                # Get the agent's action
                action = actor.execute(global_state)
                agent_writer.write(params, episode_id, step_id + 1, "actor", actor.messages)
                agent_state.action = action
                log.info(f"  Action: {action}")

                # Create details row
                details_row = details_manager.create()
                details_row.step_id = step_id + 1
                details_row.feedback = env_state.feedback
                details_row.location = env_state.location
                details_row.description = env_state.description
                details_row.inventory = env_state.inventory
                details_row.score = env_state.score
                details_row.final_reward = env_state.reward
                details_row.is_done = env_state.is_done
                details_row.thought = agent_state.thought
                details_row.action = agent_state.action
                details_manager.add(details_row)

                # Handle end of episode
                if env_state.is_done:
                    final_reward = env_state.reward
                    break

                # Sleep for n seconds to avoid API throttling
                time.sleep(sleep_time)
                log.info("")

            # Post-episode steps
            review = reviewer.review(
                global_state,
                episode["task"],
                episode["solution"])
            agent_writer.write(params, episode_id, step_id + 1, "reviewer", reviewer.messages)
            review_writer.write(review, params, episode_id)
            log.info("# Review")
            log.info("Steps: ")
            for step_id, step_analysis in review.steps.items():
                log.info(f"  {step_id}: {step_analysis}")
            log.info(f"Loops: {review.loops}")
            log.info(f"Summary: {review.summary}")
            log.info(f"Category: {review.category}")
            log.info(f"Advice: {review.advice}")

        except Exception as e:
            error_message = f"{type(e).__name__}: {e}\n" \
                + traceback.format_exc()
            result_row.error = error_message
            log.error(error_message)

        # Log the results
        log.info(f"Reward: {final_reward}")
        log.head("--- End of task ---\n")
        log.close()

        # Update result row
        total_sleep_time = sleep_time * (step_id + 1)
        result_row.stop_time = time.time()
        result_row.total_time = result_row.stop_time - result_row.start_time - total_sleep_time
        result_row.success = final_reward == 1.0
        result_row.reward = final_reward
        result_row.steps = step_id + 1
        result_row.max_steps = params.max_steps
        result_row.solution_steps = episode["solution_steps"]
        result_row.input_tokens = model.input_tokens
        result_row.output_tokens = model.output_tokens
        result_row.total_tokens = model.total_tokens
        result_row.input_cost = cost_calculator.get_input_cost(params.model_name, model.input_tokens)
        result_row.output_cost = cost_calculator.get_output_cost(params.model_name, model.output_tokens)
        result_row.total_cost = result_row.input_cost + result_row.output_cost
        result_row.reward_per_step = final_reward / (step_id + 1)
        result_row.reward_per_token = (final_reward / model.total_tokens) if model.total_tokens > 0 else 0.0
        results_manager.add(result_row)

        # Save the details
        details_manager.save()

        # Write the state
        state_writer.write(global_state, params, episode_id)

        # Sleep for n seconds to avoid API throttling
        time.sleep(sleep_time)

    # Save the results
    results_manager.save()

    # Save the summary
    results = results_manager.get_table()
    summary = summary_manager.summarize(results)
    summary_manager.append(summary)

    # Display the summaries
    print(f"Total Tasks: {summary.tasks}")
    print(f"Correct Tasks: {summary.successes}")
    print(f"Accuracy: {summary.accuracy:.0%}")
    print(f"Total Tokens: {summary.total_tokens}")
    print(f"Total Cost: ${summary.total_cost:.2f}")
    print(f"Total Time: {summary.total_time:.2f} seconds")
    print(f"Avg Reward per Task: {summary.avg_reward_per_task:.2f}")
    print(f"Avg Reward per Step: {summary.avg_reward_per_step:.4f}")
    print(f"Avg Reward per Token: {summary.avg_reward_per_token:.6f}")
    print(" --- END OF EVAL ---" )
    print("")

