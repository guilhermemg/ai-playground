from arxiv_paper_summarizer import ArxivPaperSummarizer

def main():
    summarizer = ArxivPaperSummarizer()
    results = summarizer.reprocess_all_papers()
    
    # Print summary
    print("\nProcessing Summary:")
    print("-------------------")
    successful = len([r for r in results if 'error' not in r])
    failed = len([r for r in results if 'error' in r])
    print(f"Successfully processed: {successful}")
    print(f"Failed to process: {failed}")
    
    if failed > 0:
        print("\nFailed papers:")
        for result in results:
            if 'error' in result:
                print(f"- {result['id']}: {result['error']}")

if __name__ == "__main__":
    main() 