import os
import logging

from composio_lyzr import Action, ComposioToolset
from lyzr_automata import Agent, Logger, Task
from lyzr_automata.ai_models.openai import OpenAIModel
from lyzr_automata.pipelines.linear_sync_pipeline import LinearSyncPipeline
from lyzr_automata.tasks.task_literals import InputType, OutputType
from dotenv import load_dotenv

load_dotenv()
# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Retrieve the OpenAI API key from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Exit if the API key is not set
if OPENAI_API_KEY is None:
    logging.error(
        "OPENAI_API_KEY environment variable is not set. Please configure it in the .env file."
    )
    exit(1)

# Initialize the OpenAI text completion model with the specified API key and model parameters
open_ai_text_completion_model = OpenAIModel(
    api_key=OPENAI_API_KEY, parameters={"model": "gpt-4-turbo"}
)

# Retrieve tools from the ComposioToolset for interacting with Notion and Slack
composio_notionget_tool = ComposioToolset().get_lyzr_tool(
    Action.NOTION_SEARCH_NOTION_PAGE
)
composio_notion_tool = ComposioToolset().get_lyzr_tool(Action.NOTION_CREATE_NOTION_PAGE)
composio_slack_tool = ComposioToolset().get_lyzr_tool(Action.SLACK_LIST_SLACK_MESSAGES)
composio_sendslack_tool = ComposioToolset().get_lyzr_tool(
    Action.SLACK_SEND_SLACK_MESSAGE
)


class Lyzrbase:
    def __init__(self, topic):
        self.topic = topic
        self.agents = self.initialize_agents()
        self.tasks = self.initialize_tasks()
        logging.info("Initialization of agents and tasks completed.")

    def initialize_agents(self):
        logging.info("Initializing agents...")
        agents =  {
            "researcher": Agent(
                role=f"{self.topic} Senior Data Researcher",
                prompt_persona=f"Uncover cutting-edge developments in {self.topic}. You're a seasoned researcher with a knack for uncovering the latest developments in {self.topic}. Known for your ability to find the most relevant information and present it in a clear and concise manner.",
            ),
            "analyst": Agent(
                role=f"{self.topic} Senior Data Analyst",
                prompt_persona=f"Analyze and report on {self.topic}. You're a meticulous analyst with a keen eye for detail. You're known for your ability to turn complex data into clear and concise reports, making it easy for others to understand and act on the information you provide.",
            ),
            "notion": Agent(
                role="Notion updater",
                prompt_persona="You take action on Notion using the Notion API. You are an AI agent responsible for taking actions on Notion on users' behalf using Notion APIs.",
            ),
            "slack": Agent(
                role="Slack Updater",
                prompt_persona="You are an AI agent responsible for taking actions on Slack on users' behalf using Slack APIs.",
            ),
        }
        logging.info("Initialization of agents and tasks completed.")
        return agents
    
    def initialize_tasks(self):
        if not hasattr(self, 'agents'):
            logging.error("Agents must be initialized before tasks.")
            raise Exception("Agents must be initialized before tasks.")
        
        logging.info("Initializing tasks...")
        tasks = {}
        tasks["research_task"] = Task(
                name="Research task",
                agent=self.agents["researcher"],
                output_type=OutputType.TEXT,
                input_type=InputType.TEXT,
                model=open_ai_text_completion_model,
                log_output=True,
                instructions=f"Conduct a thorough research about {self.topic}. Ensure you find any interesting and relevant information given the current year is 2024.",
            )
        tasks["reporting_task"] = Task(
                name="Reporting task",
                agent=self.agents["analyst"],
                output_type=OutputType.TEXT,
                input_type=InputType.TEXT,
                model=open_ai_text_completion_model,
                input_tasks=[tasks["research_task"]],
                log_output=True,
                instructions="Review the context you received and expand each topic into a full section for a report. Ensure the report is detailed and contains all relevant information.",
            )
        tasks["notion_get_task"] = Task(
                name="Notion get task",
                agent=self.agents["notion"],
                tool=composio_notionget_tool,
                model=open_ai_text_completion_model,
                log_output=True,
                instructions="Retrieve the page ID you want to update on Notion.",
            )
        tasks["notion_task"] =  Task(
                name="Notion task",
                agent=self.agents["notion"],
                tool=composio_notion_tool,
                model=open_ai_text_completion_model,
                log_output=True,
                input_tasks=[
                    tasks["reporting_task"],
                    tasks["notion_get_task"],
                ],
                instructions="Create a document on Notion that summarizes the report.",
            )
        tasks["slack_task"] = Task(
                name="Slack messaging",
                agent=self.agents["slack"],
                log_output=True,
                tool=composio_slack_tool,
                model=open_ai_text_completion_model,
                instructions="List the latest Slack message in the specified channel ID.",
            )
        tasks["slack_send_task"] = Task(
                name="Slack send",
                log_output=True,
                agent=self.agents["slack"],
                tool=composio_sendslack_tool,
                model=open_ai_text_completion_model,
                input_tasks=[tasks["notion_task"]],
                instructions="Send a message on the Slack channel 'random' that summarizes the complete research activity. Include a summary of your findings and attach the report.",
            )
        logging.info("Tasks initialized successfully.")
        return tasks

    def run_pipeline(self):
        if not hasattr(self, 'tasks'):
            logging.error("Tasks are not initialized.")
            raise Exception("Tasks are not initialized.")
        logging.info("Running pipeline...")
        LinearSyncPipeline(
            name="Composio pipeline",
            logger=Logger(),
            completion_message="Pipeline completed successfully.",
            tasks=[
                self.tasks["research_task"],
                self.tasks["reporting_task"],
                self.tasks["notion_get_task"],
                self.tasks["notion_task"],
                self.tasks["slack_task"],
                self.tasks["slack_send_task"],
            ],
        ).run()
        logging.info("Pipeline completed successfully.")

    def main(self):
        self.run_pipeline()
