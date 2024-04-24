
from lyzr_automata import Task, Agent
from lyzr_automata.ai_models.openai import OpenAIModel
from composio_lyzr import ComposioToolset, App, Action
from lyzr_automata.pipelines.linear_sync_pipeline import LinearSyncPipeline
import os
from lyzr_automata.tasks.task_literals import InputType, OutputType
from lyzr_automata import Logger


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if OPENAI_API_KEY is None:
    print("Please set OPENAI_API_KEY environment variable in the .env file")
    exit(1)

open_ai_text_completion_model = OpenAIModel(api_key=OPENAI_API_KEY, parameters={"model": "gpt-4-turbo"})

#you can uncomment the below code to only allow a specific toolset from the composio toolset
composio_notionget_tool = ComposioToolset().get_lyzr_tool(Action.NOTION_SEARCH_NOTION_PAGE)
composio_notion_tool = ComposioToolset().get_lyzr_tool(Action.NOTION_CREATE_NOTION_PAGE)
composio_slack_tool = ComposioToolset().get_lyzr_tool(Action.SLACK_LIST_SLACK_MESSAGES)
composio_sendslack_tool = ComposioToolset().get_lyzr_tool(Action.SLACK_SEND_SLACK_MESSAGE)

class Lyzrbase:
    
    def main(input):
        topic = input
        
        researcher = Agent(
            role=f"{topic} Senior Data Researcher",
            prompt_persona=f"Uncover cutting-edge developments in {topic}\nYou're a seasoned researcher with a knack for uncovering the latest\ndevelopments in {topic}. Known for your ability to find the most relevant\ninformation and present it in a clear and concise manner."
        )
        analyst = Agent(
                    role=f"{topic} Senior Data Analyst",
                    prompt_persona=f"Analyze and report on {topic}\nYou're a meticulous analyst with a keen eye for detail. You're known for\nyour ability to turn complex data into clear and concise reports, making\nit easy for others to understand and act on the information you provide."
                )
        notion = Agent (
                    role="Notion updater",
                    prompt_persona="You take action on Notion using the Notion API\nYou are AI agent that is responsible for taking actions on Notion on \nusers behalf. You need to take action on Notion using Notion APIs"
                )
        slack =  Agent(
                    role="Slack Updater",
                    prompt_persona="You are AI agent that is responsible for taking actions on Slack on \nusers behalf. You need to take action on Slack using Slack APIs"
                )
        research_task =  Task(
                name="Research task",
                agent=researcher,
                output_type=OutputType.TEXT,
                input_type=InputType.TEXT,
                model=open_ai_text_completion_model,
                log_output=True,
                instructions=f"Conduct a thorough research about {topic}\nMake sure you find any interesting and relevant information given\nthe current year is 2024."
            )

        reporting_task = Task(
                name="Reporting task",
                agent=analyst,
                output_type=OutputType.TEXT,
                input_type=InputType.TEXT,
                model=open_ai_text_completion_model,
                input_tasks=[research_task],
                log_output=True,
                instructions=f"Review the context you got and expand each topic into a full section for a report.\nMake sure the report is detailed and contains any and all relevant information."
            )
        notion_get_task = Task(
                name="Notion get task",
                agent= notion,
                tool=composio_notionget_tool,
                model=open_ai_text_completion_model,
                log_output=True,
                instructions="Get the page id you want to update on notion."
            )
        notion_task = Task(
                name="Notion task",
                agent= notion,
                tool=composio_notion_tool,
                model=open_ai_text_completion_model,
                log_output=True,
                input_tasks=[reporting_task, notion_get_task],
                instructions="Write a document on notion that summarizes the report"
            )
        slack_task =  Task(
                name="Slack messaging",
                agent=slack,
                log_output = True,
                tool=composio_slack_tool,
                model=open_ai_text_completion_model,
                instructions="List the latest slack message in the random channel id"
            )
        slack_send_task = Task(
            name="Slack send",
            log_output=True,
            agent=slack,
            tool=composio_sendslack_tool,
            model=open_ai_text_completion_model,
            input_tasks=[notion_task],
            instructions="Write a message on slack channel 'random' that summarizes complete research activity. Write a summary of your findings and attach the report."
        )

        LinearSyncPipeline(
            name="Composio pipeline",
            logger=Logger(),
                # completion message after pipeline completes
            completion_message="pipeline completed",
            tasks=[
                research_task,
                reporting_task,
                notion_get_task,
                notion_task,
                slack_task,
                slack_send_task
            ],
        ).run()

