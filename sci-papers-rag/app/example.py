from main import ArxivPaperSummarizer

def main():
    summarizer = ArxivPaperSummarizer()
    
    # Summarize papers about quantum computing
    summaries = summarizer.summarize_topic("self correct rag", max_papers=4)
    
    # Print results
    for summary in summaries:
        print(f"\nTitle: {summary['title']}")
        print(f"Authors: {', '.join(summary['authors'])}")
        print(f"Summary: {summary['summary']}")
        print(f"URL: {summary['url']}")
        print(f"Published: {summary['published']}")
        print("-" * 80)

if __name__ == "__main__":
    main() 