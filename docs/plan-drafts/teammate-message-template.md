<teammate-message teammate_id="team-lead"> You are the project leader for MHE research-loop long-term schematization and next-slice implementation planning. You may edit exactly one file for this task: docs/plan-drafts/plan-v4.md. Do not edit code and do not touch unrelated staged/untracked files.

Goal:

Create docs/plan-drafts/plan-v4.md as the next document after plan-v3.
User has approved using the project-leader-teammate workflow: blueprint > plan = roadmap timescale; one blueprint has multiple phases; each phase has a user-facing plan and an agent-facing roadmap; roadmap enhances plan with implementation details.
The immediate selected direction should be the MVP-adjacent next slice: wire a thin research-run CLI and example input so the already-implemented Research Loop MVP becomes user-facing, without claiming Phase N discovery.

Current evidence:

P0a-P4 research-loop MVP is implemented and independently verified.
Recent commits include lifecycle models, mappers/store, FEALPy walking skeleton, minimal orchestrator, FEALPy rule-based designer, reviewer calibration, HypothesisActionSpace, ResearchDossier/NegativeResultAggregator, and formatting.
Validation known: python -m pytest tests/test_research_*.py -q passed 36 tests; Ruff check on research-loop files passed.
Independent verifier said no blockers; non-blocking follow-up: research-run CLI not wired, but focused tests satisfied P1.

Repo context:

docs/plan-drafts/plan-v3.md contains the prior MVP/vision plan.
Existing unrelated working-tree changes include .mhe approvals/evidence and benchmark docs/tests; do not modify them.

Write plan-v4.md in Chinese, with concise but implementation-ready structure:

Document positioning and relation to plan-v3.
Blueprint/plan/roadmap timescale definitions.
Current completed baseline and evidence.
Selected next direction: CLI/user-facing MVP execution path.
Non-goals/non-claims.
Plan: user-facing goals and acceptance criteria.
Roadmap: agent-facing steps with target files, expected artifacts, validation commands, and commit boundaries.
Future phase options after CLI slice.
Reviewer/verifier gates and handoff notes.

Keep it focused. Do not invent results. Do not say the CLI already exists. After writing, report what you wrote and any implementation recommendations under 250 words.
</teammate-message>

 introduce how did you call the team-lead (donnot load skill now)                   

● I did not load a skill or spawn a new agent.

  team-lead was already an active teammate in the session and sent me
  <teammate-message ...>. I replied to it using the built-in SendMessage tool,
  addressed by teammate name:

  {
    "to": "team-lead",
    "summary": "plan-v4 already written",
    "message": "...status update..."
  }
  <teammate-message ...>. I replied to it using the built-in SendMessage tool,
  addressed by teammate name:

  {                                                       
    "to": "team-lead",                       
    "summary": "plan-v4 already written",  
    "message": "...status update..."                
  }
                                                                            
  So the flow was:
                                                                                     
  1. Receive <teammate-message teammate_id="team-lead">...
  2. Inspect or verify local files if needed.                      
  3. Call SendMessage with to: "team-lead".
  4. Include a short summary and plain-text message.

  I did not invoke /project-leader-teammate or any OMC skill for that reply.
                              
❯ how did you created the leader teammate (donnot load skill now)                    
                              
● I didn’t create the team-lead teammate in this turn/session flow.
                                                         
  What happened here:
                                                         
  - The teammate already existed and sent me messages via <teammate-message 
  teammate_id="team-lead">....
  - I only responded to that existing teammate using SendMessage.
  - I did not call TeamCreate.
  - I did not call Agent.
  - I did not load /project-leader-teammate or any skill.

  In general, a leader teammate can be created either by:                   
                                                                                    
  TeamCreate({                                        
    "team_name": "...",
    "description": "...",                                                            
    "agent_type": "..."
  })                                                                                 
                                                                                   
  then spawning an agent into that team with a name like team-lead, or by an       
  orchestration/skill workflow that sets up the leader before I receive messages. In
  this case, it was already present before my replies.
