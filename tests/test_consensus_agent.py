from app.agents.consensus_agent import run_consensus

def test_consensus():
    query = "How are sales doing this year?"
    result = run_consensus(query)
    print(f"Query: {query}")
    print(f"Result: {result}")
    assert "Reconciled Insight" in result
    print("Test passed successfully!")

if __name__ == "__main__":
    test_consensus()
