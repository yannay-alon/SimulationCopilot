from typing import Literal

from pydantic import BaseModel, Field, field_validator, ValidationInfo, ValidationError


class Cadet(BaseModel):
    name: str
    interview_answers: dict[str, str]


class PastSimulation(BaseModel):
    filename: str
    content: str
    score: int | None = None


class SimulatorBrief(BaseModel):
    role: str = Field(description="The role that the person simulating the cadet will take on")
    content: str = Field(
        description="The brief for the person simulating the cadet. This should include instructions on how to simulate the cadet, what information to use from the interview answers, and any other relevant details.")
    cases_and_responses: dict[str, str] = Field(
        description="A mapping of possible cases that could arise during the simulation and how the simulator should respond to them. This is meant to help the simulator react in a way that is consistent with the cadet's profile and the simulation's goals.")


class SimulatedBrief(BaseModel):
    background: str = Field(
        description="Background information for the simulated cadet, their simulated role, unit, and any other important details for the cadet to understand the simulation")


class SimulationOutput(BaseModel):
    subject: str = Field(description="The main challenge the simulation tests for")
    research_question: str = Field(
        description="A question that connects the subject of the simulation to the weekly theme")
    simulation_type: Literal["Formal", "Eruptive", "Personal"] = Field(
        description="Either a formal, a eruptive, or a personal simulation")
    target_challenge: str = Field(
        description="What challenges will the cadet be facing? What dilemmas or complexities arise from it?")
    simulation_workflow: str = Field(
        description="The full simulation workflow. This should contain the background, the scene in which the simulation occurs, etc. Somewhat like a script for a play."
    )
    cadet_goals: str = Field(description="What are the cadet’s goals and how do they relate to the simulation?")
    simulated_cadet_brief: SimulatedBrief | None = Field(
        description="The brief for the simulated cadet (if the simulation is not a eruptive simulation)")
    simulators_briefs: list[SimulatorBrief] = Field(description="Briefs for the people who simulate the cadet")
    red_lines: list[str] = Field(description="Conditions for when we should stop the simulation")
    fading_actions: dict[str, str] = Field(
        description="How will you act when the simulation fades (additional twists). Describe each possible fading scenario and how you will react")
    discussion_questions: list[str] = Field(description="Questions for the team’s discussion after the simulation")
    practical_tools: list[str] = Field(
        description="Practical tools or thumb-rules that can be learnt from the simulation (if any)")

    @field_validator("simulated_cadet_brief")
    @classmethod
    def simulated_cadet_brief_required_if_not_eruptive(
            cls, value: SimulatedBrief | None,
            info: ValidationInfo
    ) -> SimulatedBrief | None:
        if info.data['simulation_type'].lower() == "eruptive":
            return None
        if value is None:
            raise ValidationError("simulated_cadet_brief is required for non-eruptive simulations")
        return value
    
    def get_simulation_type_display_name(self) -> str:
        match self.simulation_type:
            case "Formal":
                return "סימולציה פורמלית"
            case "Eruptive":
                return "סימולציה מתפרצת"
            case "Personal":
                return "סימולציה אישית"
            case _:
                raise ValueError(f"Unknown simulation type: {self.simulation_type}")

class MultipleSimulations(BaseModel):
    simulations: dict[str, SimulationOutput] = Field(
        description="Multiple simulations for different cadets. The key is the name of the cadet being simulated and the value is the simulation output for that cadet."
    )


class AgentDecision(BaseModel):
    is_draft_needed: bool = Field(
        description="Whether the user is ready and requesting to generate or update the full simulation draft. Set to False if the user is just brainstorming, discussing ideas, or if you need to ask clarifying questions."
    )
    next_step_directions: str = Field(
        default=False,
        description="When a draft is not needed, write directions for the follow-up AI agent what should be done - asking clarification questions, discussing ideas, etc."
    )