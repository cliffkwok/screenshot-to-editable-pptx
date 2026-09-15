"""Run all parts together."""
exec(open("reconstruct_part1.py").read())
exec(open("reconstruct_part2.py").read())
exec(open("reconstruct_part3.py").read())
exec(open("reconstruct_part4.py").read())
exec(open("reconstruct_part5.py").read())

out = "ADK_agent_workflow.pptx"
prs.save(out)
print(f"Saved: {out}")