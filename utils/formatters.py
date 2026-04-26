from models.domain_models import MultipleSimulations

class OutputFormatter:
    @staticmethod
    def format_draft(draft: MultipleSimulations) -> dict[str, str]:
        all_drafts = dict()
        for cadet_name, sim_output in draft.simulations.items():
            
            discussion_questions = "\n\n".join([f"- {q}" for q in sim_output.discussion_questions])
            practical_tools = "\n\n".join([f"- {t}" for t in sim_output.practical_tools])
            red_lines = "\n\n".join([f"- {rl}" for rl in sim_output.red_lines])
            
            fading_actions = "\n\n".join([f"- **{k}:** {v}" for k, v in sim_output.fading_actions.items()])

            simulators_briefs = []
            for simulator_brief in sim_output.simulators_briefs:
                cases_responses = "\n\n".join([f"  - **{k}:** {v}" for k, v in simulator_brief.cases_and_responses.items()])
                
                simulators_briefs.append(f"""\
### תפקיד:
    
{simulator_brief.role}
    
### תדריך:
    
{simulator_brief.content}
    
### מקרים ותגובות:
    
{cases_responses}
""")
            simulators_briefs = "\n\n".join(simulators_briefs)
            
            simulated_cadet_brief = sim_output.simulated_cadet_brief.background if sim_output.simulated_cadet_brief else "No brief available"
            
            single_draft = f"""
<details>
<summary>סימולציה עבור {cadet_name}</summary>

**נושא:** {sim_output.subject}

**שאלת מחקר:** {sim_output.research_question}

**סוג סימולציה:** {sim_output.get_simulation_type_display_name()}

**מטרת הסימולציה ביחס לצוער המסומלץ:**

{sim_output.target_challenge}

**תיאור הסימולציה:**

{sim_output.simulation_workflow}

**יעדי הצוער:**

{sim_output.cadet_goals}

**תדרוכים:**

## תדריך למסמלץ:

{simulated_cadet_brief}

## תדריך למסמלצים:

{simulators_briefs}

**קווים אדומים:**

{red_lines}
  
**פעולות במקרה של דעיכה:**

{fading_actions}

**שאלות לדיון:**

{discussion_questions}

**כלים פרקטיים:**

{practical_tools}

</details>
"""
            all_drafts[cadet_name] = single_draft

        return all_drafts