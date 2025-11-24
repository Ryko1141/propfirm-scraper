"""
LLM-powered rule extraction using local Ollama models.
"""

import json
from pathlib import Path

import ollama


LLM_PROMPT = """You are a specialized data extraction assistant analyzing prop trading firm rules.

Extract ALL trading rules from the following HTML content. Include both hard rules (explicit limits/prohibitions) 
and soft rules (general guidelines, recommendations, best practices).

CRITICAL: Return ONLY valid JSON matching this exact structure - no markdown, no explanations:

{{
  "account_sizes": ["50000", "100000"],
  "profit_targets": ["10"],
  "daily_loss_limit": "5",
  "max_drawdown": "10",
  "prohibited_strategies": ["copy trading", "HFT", "martingale"],
  "profit_split": "80",
  "min_trading_days": 5,
  "leverage": "1:100",
  "soft_rules": [
    "Consistent trading strategy recommended",
    "Risk management encouraged"
  ]
}}

HTML Content:
{content}

JSON:"""


def query_llm(text, model='qwen2.5-coder:14b'):
    """Query local LLM to extract rules from text."""
    prompt = LLM_PROMPT.format(content=text[:4000])  # Limit context length
    
    try:
        response = ollama.generate(
            model=model,
            prompt=prompt,
            options={
                'temperature': 0.1,
                'num_predict': 500,
            }
        )
        
        result_text = response['response'].strip()
        
        # Clean up markdown code blocks if present
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
            result_text = result_text.strip()
        
        return json.loads(result_text)
    
    except json.JSONDecodeError as e:
        print(f"    ⚠ LLM returned invalid JSON: {e}")
        return None
    except Exception as e:
        print(f"    ⚠ LLM error: {e}")
        return None


def extract_with_llm(input_file, output_file='output/rules_llm.json', model='qwen2.5-coder:14b'):
    """Run LLM-based extraction on all pages."""
    print(f"Loading scraped pages from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        pages = json.load(f)
    
    results = []
    print(f"Extracting rules using LLM ({model}) from {len(pages)} pages...")
    print("⚠ This may take 15-30 minutes depending on model size.\n")
    
    for idx, page in enumerate(pages, 1):
        title = page.get('title', 'Untitled')
        url = page.get('url', '')
        text = page.get('html', page.get('body', ''))
        
        print(f"[{idx}/{len(pages)}] Processing: {title}")
        
        llm_result = query_llm(text, model=model)
        
        if llm_result:
            llm_result['source'] = url
            llm_result['title'] = title
            results.append(llm_result)
            print(f"    ✓ Extracted {len(llm_result.get('prohibited_strategies', []))} prohibited strategies")
        else:
            print(f"    ✗ Failed to extract")
        
        # Save progress every 10 pages
        if idx % 10 == 0:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"    💾 Progress saved ({idx}/{len(pages)} pages)")
    
    # Final save
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open('w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Completed extraction for {len(results)} pages")
    print(f"✓ Results saved to {output_file}")
    
    return results


if __name__ == "__main__":
    import sys
    
    input_file = sys.argv[1] if len(sys.argv) > 1 else "output/scraped_pages.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output/rules_llm.json"
    model = sys.argv[3] if len(sys.argv) > 3 else "qwen2.5-coder:14b"
    
    extract_with_llm(input_file, output_file, model)
