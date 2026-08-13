import subprocess
from groq import Groq
import os

def get_recent_changes():
    """Get the diff of the most recent commit."""
    result = subprocess.run(
        ["git", "diff", "HEAD~1", "HEAD", "--", "my_first_agent"],
        capture_output=True, text=True
    )
    return result.stdout


def summarize_changes(diff_text):
    if not diff_text.strip():
        return None  # nothing changed, nothing to summarize

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Summarize this code change in 2-3 clear sentences, "
                                            "for a README changelog. Focus on WHAT changed and WHY it matters, "
                                            "not line-by-line details."},
            {"role": "user", "content": diff_text[:4000]}  # keep it reasonable in size
        ]
    )
    return response.choices[0].message.content


def update_readme(summary):
    if not summary:
        print("No changes to summarize.")
        return

    with open("README.md", "a") as f:
        f.write(f"\n\n## Recent Update\n{summary}\n")

    print("README updated with:")
    print(summary)


if __name__ == "__main__":
    diff = get_recent_changes()
    summary = summarize_changes(diff)
    update_readme(summary)