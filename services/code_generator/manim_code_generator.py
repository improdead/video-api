import os
import logging
import google.generativeai as genai
from typing import Dict, Any, List
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not found in environment variables")

async def generate_manim_code(scene: Dict[str, Any], index: int) -> str:
    """
    Generate Manim code for a scene using Gemini AI
    
    Args:
        scene: The scene description
        index: The scene index
        
    Returns:
        str: The generated Manim code
    """
    try:
        logger.info(f"Generating Manim code for scene {index + 1}")
        
        # If no API key, return a mock code for development
        if not GEMINI_API_KEY:
            logger.warning("Using mock code generator as GEMINI_API_KEY is not set")
            return generate_mock_code(scene, index)
        
        # Configure the model
        model = genai.GenerativeModel('gemini-pro')
        
        # Create the prompt for Gemini
        gemini_prompt = f"""Generate Manim Python code for the following scene description: "{scene['visualDescription']}"
        
        This should be scene #{index + 1} running from {scene['startTime']} to {scene['endTime']}.
        
        Generate a complete, executable Manim Python class that extends Scene. The code should:
        1. Create appropriate mathematical visualizations based on the description
        2. Use appropriate animations with proper timing
        3. Include any necessary text elements that match the narration: "{scene['narration']}"
        4. Be fully self-contained and runable as a single file
        5. Use best practices for clean, efficient Manim code
        
        Return ONLY the Python code without any explanations or markdown.
        
        Make sure the class name is unique and includes the scene number, like 'Scene{index + 1}' or similar.
        
        The code should work with Manim Community Edition.
        """
        
        # Generate content
        response = await model.generate_content_async(gemini_prompt)
        
        # Extract the code from the response
        text_response = response.text
        
        # Try to extract code if it's wrapped in markdown code blocks
        code_match = re.search(r'```python\n([\s\S]*?)\n```', text_response) or \
                     re.search(r'```\n([\s\S]*?)\n```', text_response)
        
        if code_match:
            code = code_match.group(1)
        else:
            code = text_response
        
        # Ensure the code has a proper class name
        code = ensure_proper_class_name(code, index)
        
        logger.info(f"Successfully generated Manim code for scene {index + 1}")
        return code
        
    except Exception as e:
        logger.exception(f"Error generating Manim code for scene {index + 1}: {str(e)}")
        # Fall back to mock code in case of error
        return generate_mock_code(scene, index)

def ensure_proper_class_name(code: str, index: int) -> str:
    """
    Ensure the Manim code has a proper class name
    
    Args:
        code: The Manim code
        index: The scene index
        
    Returns:
        str: The code with a proper class name
    """
    # Check if there's a class definition
    class_match = re.search(r'class\s+(\w+)\s*\(\s*Scene\s*\)', code)
    
    if class_match:
        current_class_name = class_match.group(1)
        desired_class_name = f"Scene{index + 1}"
        
        # If the class name doesn't include the scene number, replace it
        if f"Scene{index + 1}" not in current_class_name:
            code = code.replace(
                f"class {current_class_name}(Scene)",
                f"class {desired_class_name}(Scene)"
            )
    else:
        # If no class definition found, add one
        code = f"""from manim import *

class Scene{index + 1}(Scene):
    def construct(self):
        # Fallback implementation
        title = Text("Scene {index + 1}")
        self.play(Write(title))
        self.wait(2)
        self.play(FadeOut(title))
"""
    
    return code

def generate_mock_code(scene: Dict[str, Any], index: int) -> str:
    """
    Generate mock Manim code for development purposes
    
    Args:
        scene: The scene description
        index: The scene index
        
    Returns:
        str: Mock Manim code
    """
    narration = scene["narration"]
    visual_desc = scene["visualDescription"]
    
    # Create a simple scene based on the index
    if index == 0:
        # Title scene
        return f"""from manim import *

class Scene{index + 1}(Scene):
    def construct(self):
        # Title scene
        title = Text("{narration}")
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        
        # Create a circle that pulses
        circle = Circle(radius=2, color=BLUE)
        self.play(Create(circle))
        
        # Pulse animation
        self.play(circle.animate.scale(1.2), rate_func=there_and_back)
        self.play(circle.animate.scale(1.2), rate_func=there_and_back)
        
        self.wait(1)
"""
    elif index == 1:
        # Equation scene
        return f"""from manim import *

class Scene{index + 1}(Scene):
    def construct(self):
        # Equation scene
        title = Text("{narration}", font_size=24)
        title.to_edge(UP)
        self.add(title)
        
        # Create an equation
        equation = MathTex("x^2 + y^2 = r^2")
        
        # Animate each part
        self.play(Write(equation))
        
        # Highlight parts of the equation
        self.play(equation.animate.set_color_by_tex("x^2", YELLOW))
        self.wait(0.5)
        self.play(equation.animate.set_color_by_tex("y^2", GREEN))
        self.wait(0.5)
        self.play(equation.animate.set_color_by_tex("r^2", RED))
        
        self.wait(1)
"""
    elif index == 2:
        # Visual example scene
        return f"""from manim import *

class Scene{index + 1}(Scene):
    def construct(self):
        # Visual example scene
        title = Text("{narration}", font_size=24)
        title.to_edge(UP)
        self.add(title)
        
        # Create a coordinate system
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            axis_config={{"color": BLUE}}
        )
        
        # Add labels
        x_label = axes.get_x_axis_label("x")
        y_label = axes.get_y_axis_label("y")
        
        self.play(Create(axes), Write(x_label), Write(y_label))
        
        # Create a function graph
        graph = axes.plot(lambda x: x**2, color=RED)
        graph_label = MathTex("f(x) = x^2").next_to(graph, UP)
        
        self.play(Create(graph), Write(graph_label))
        
        # Show a point moving along the graph
        dot = Dot(color=YELLOW)
        dot.move_to(axes.c2p(-2, 4))
        
        self.play(FadeIn(dot))
        
        self.play(
            dot.animate.move_to(axes.c2p(2, 4)),
            rate_func=lambda t: t,
            run_time=3
        )
        
        self.wait(1)
"""
    else:
        # Summary scene
        return f"""from manim import *

class Scene{index + 1}(Scene):
    def construct(self):
        # Summary scene
        title = Text("{narration}", font_size=24)
        title.to_edge(UP)
        self.add(title)
        
        # Create bullet points
        points = [
            "Key point 1 about the topic",
            "Key point 2 about the topic",
            "Key point 3 about the topic"
        ]
        
        bullets = VGroup()
        for i, point in enumerate(points):
            bullet = Text("• " + point, font_size=24)
            bullets.add(bullet)
        
        bullets.arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        bullets.next_to(title, DOWN, buff=1)
        
        # Animate each bullet point
        for bullet in bullets:
            self.play(Write(bullet))
            self.wait(0.5)
        
        # Final animation
        final_equation = MathTex("E = mc^2")
        final_equation.next_to(bullets, DOWN, buff=1)
        
        self.play(Write(final_equation))
        self.play(final_equation.animate.scale(1.5).set_color(YELLOW))
        
        self.wait(1)
"""
