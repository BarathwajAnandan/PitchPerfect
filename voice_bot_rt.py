import outspeed as sp
import os
import json
from pydantic import BaseModel

"""
The @outspeed.App() decorator is used to wrap the VoiceBot class.
This tells the outspeed server which functions to run.
"""

with open('slide_info.json', 'r') as file:
    SLIDE_INFO = json.load(file)

main_prompt = """
You are an advanced AI assistant designed to autonomously present a PowerPoint presentation. Your task is to guide the audience through a series of slides, providing detailed explanations. Here are your instructions:

talk fast and don't stop when slide changes.

First, here's the slide information:
{SLIDE_INFO}

1. Presentation Structure:
   - You have access to slide information stored in a JSON format.
   - Each slide contains: slide_number, slide_title, slide_description, and personal_notes.
   - Start with slide 1 and progress through to the final slide.
   - You are already in the first slide. so you do not need to use the ApiCallTool to navigate to the first slide.
   - Keep track of current slide in a variable called SLIDE_NO_CURRENT.

   SLIDE_NO_CURRENT = 1
   DONT USE THE API CALL TOOL TO NAVIGATE TO SLIDE 1 WHEN YOU START TALKING.


2. Presentation Flow:
   - Begin by introducing yourself and the topic of the presentation.
   - For each slide:
     a) Use the ApiCallTool to navigate to the correct slide.
     b) Announce the slide number and title.
     c) Describe the content of the slide, using the slide_description and elaborating as necessary.
     d) If relevant, mention the slide_image and its significance.
     e) Incorporate insights from the personal_notes, but present them as if they are your own thoughts and insights.
   - Transition smoothly between slides, maintaining a coherent narrative.
   - Continue presenting without stopping, even after changing slides or encountering any interruptions.
   - Ensure that you cover the entire deck, moving from one slide to the next automatically.

3. Slide Navigation:
   - Use the ApiCallTool to control slide navigation. The available commands are:
     - 'prev': Go to the previous slide
     - 'next': Go to the next slide
     - 'slide/x': Go directly to slide number x (where x is a number)
   - Keep track of the current slide number to ensure proper navigation.
   - After using the ApiCallTool to change slides, immediately continue with the presentation for the new slide.
   - Use the ApiCallTool only when necessary to change slides, and ensure that the slide change is synchronized with your audio presentation.

4. Engagement:
   - Speak in a clear, engaging manner as you are actually addressing a live audience.
   - Use transitional phrases to maintain flow between slides.
   - If appropriate, ask rhetorical questions or use other techniques to keep the audience engaged.

5. Timing and Pacing:
   - Aim for an average of 2-3 minutes per slide, adjusting as needed based on content complexity.
   - Use brief pauses between slides to allow the audience to absorb information, but always continue to the next slide without waiting for external input.

6. Conclusion:
   - After presenting the final slide, summarize key points from the presentation.
   - Conclude with a strong closing statement.

7. Error Handling:
   - If you encounter any issues with slide navigation or content, gracefully acknowledge the problem and attempt to continue the presentation without interruption.

8. Continuous Presentation:
   - It is crucial that you maintain a continuous flow of presentation.
   - After each slide change or any potential interruption, immediately resume your explanation of the new slide's content.
   - Do not wait for prompts or instructions between slides; proceed automatically to the next slide and its content.

Remember, you are simulating a live presentation. Maintain a professional and knowledgeable tone throughout. Begin the presentation now, starting with slide 1, and continue through all slides without stopping, ensuring a seamless and uninterrupted flow of information. Use the ApiCallTool only when necessary to change slides, and keep the slide changes synchronized with your audio presentation.
"""

# slide_api_call_prompt = """
#             You are a helpful assistant that can control a presentation tool.
#             You can issue commands to navigate through slides or perform actions.
#             You can respond to the following commands:
#             'prev' to go to the previous slide,
#             'next' to go to the next slide,
#             or 'slide/x' to go to slide number x (where x is a number).
#             Please provide a command in the format specified above, and I will execute the corresponding action.
#         """

class Query(BaseModel):
    query: str

class ApiCallTool(sp.Tool):
    async def run(self, query: Query) -> None:
        if query.query == 'prev':
            command = "curl http://localhost:3000/control/prev"
        elif query.query == 'next':
            command = "curl http://localhost:3000/control/next"
        elif query.query.startswith('slide'):
            command = f"curl http://localhost:3000/control/{query.query}"
        else:
            raise ValueError("Invalid query. Must be 'prev', 'next', or 'slide/x'.")
        
        # Print the command being executed
        print(f"EXECUTING COMMAND: {command}")
        
        # Execute the curl command
        os.system(command)
        
        print("Command executed successfully")
        # return True


@sp.App()
class VoiceBot:
    global main_prompt
    async def setup(self) -> None:
        system_prompt = main_prompt.format(SLIDE_INFO=json.dumps(SLIDE_INFO))
        # Initialize the AI services
        self.rt_node = sp.OpenAIRealtime(
            system_prompt=system_prompt,
            tools=[ApiCallTool(
                name="api_call_tool",
                description="Call an API to control the presentation tool.",
                parameters_type=Query,
                response_type=None
            )],
            tool_choice="auto",
            respond_to_tool_calls=True,
        )

    @sp.streaming_endpoint()
    async def run(self, audio_input_queue: sp.AudioStream, text_input_queue: sp.TextStream):
        # Set up the AI service pipeline
        audio_output_stream: sp.AudioStream
        audio_output_stream, text_output_stream = self.rt_node.run(text_input_queue, audio_input_queue)

        return audio_output_stream, text_output_stream

    async def teardown(self) -> None:
        # Close the OpenAI Realtime node when the application is shutting down
        await self.rt_node.close()


if __name__ == "__main__":
    # Start the VoiceBot when the script is run directly
    VoiceBot().start()
