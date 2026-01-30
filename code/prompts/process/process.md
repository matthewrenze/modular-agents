## Start of the Episode
At the start of the episode, the environment will provide us with:
  - Task - a raw description of the task we need to complete.
  - State - the initial state of the environment.
Then, we will provide:
  - Task (Tasker) - a clear and concise description of the task to be completed.
We will complete the task through a series of steps in an iterative loop.

## Each Step of the Episode
At each step of the episode, we will be provided with:
  - Step - the current step number.
Next, the environment will provide us with:
  - Feedback - the feedback from the last action we took.
  - Location - our current location in the environment.
  - Description - the current state of the environment.
  - Inventory - the items we are currently carrying.
  - Capacity - the current and maximum number of items in inventory.
  - Score - our current score and maximum possible score.
  - Done - whether the task is complete or not.
Then, we will provide:
  - Thought (Reasoner) - a goal-oriented chain-of-reasoning from the current state to the best next action.
  - Action (Actor) - a command that we will execute in our environment.
  - Summary (Summarizer) - a summary of the state-action pair for this step.
Finally, the environment will provide us with an updated state based on our action.
We will use feedback from the environment to refine our actions in subsequent steps.

## End of the Episode
At the end of the episode, the environment will provide us with:
  - the final state of the environment (see above for details).
We will end the task by executing the "quit" operation.