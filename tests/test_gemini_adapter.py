import unittest

from kaggle_capstone_coach.gemini_adapter import GeminiModelAdapter


class FakeResponse:
    text = """
    {
      "agent_summaries": [
        {
          "name": "Requirement Analyst",
          "responsibility": "Model-backed requirement analysis.",
          "finding": "Gemini identified Kaggle Writeup and video requirements."
        },
        {
          "name": "Repo Auditor",
          "responsibility": "Model-backed repo audit.",
          "finding": "Gemini reviewed repository evidence from the MCP tools."
        },
        {
          "name": "Submission Strategist",
          "responsibility": "Model-backed prioritization.",
          "finding": "Gemini prioritized media gallery and deployability evidence."
        },
        {
          "name": "Communication Coach",
          "responsibility": "Model-backed communication support.",
          "finding": "Gemini drafted clearer judge-facing language."
        }
      ]
    }
    """


class FakeModels:
    def __init__(self):
        self.calls = []

    def generate_content(self, model, contents):
        self.calls.append({"model": model, "contents": contents})
        return FakeResponse()


class FakeClient:
    def __init__(self):
        self.models = FakeModels()


class GeminiModelAdapterTests(unittest.TestCase):
    def test_adapter_calls_gemini_client_and_returns_agent_summaries(self):
        client = FakeClient()
        adapter = GeminiModelAdapter(
            api_key="not-a-real-key",
            client=client,
            model="gemini-test-model",
        )
        context = {
            "requirement_text": "Submission Requirements include Kaggle Writeup.",
            "repo_files": ("README.md", "app.py"),
            "checklist": (),
            "security_summary": None,
        }

        summaries = adapter.build_agent_summaries(context)

        self.assertEqual(client.models.calls[0]["model"], "gemini-test-model")
        self.assertIn("Submission Requirements", client.models.calls[0]["contents"])
        self.assertEqual(len(summaries), 4)
        self.assertEqual(summaries[0]["name"], "Requirement Analyst")
        self.assertIn("Kaggle Writeup", summaries[0]["finding"])


if __name__ == "__main__":
    unittest.main()
