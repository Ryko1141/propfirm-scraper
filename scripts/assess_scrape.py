import json
import sys

# Load scraped data
file_path = sys.argv[1] if len(sys.argv) > 1 else "output/fundednext_full.json"
with open(file_path, encoding='utf-8') as f:
    data = json.load(f)

print("="*70)
print("📊 SCRAPE QUALITY ASSESSMENT")
print("="*70)

# Basic stats
print(f"\n📈 OVERALL STATS:")
print(f"   Total Pages: {len(data)}")
print(f"   Pages with content: {sum(1 for p in data if len(p.get('body', '')) > 100)}")
print(f"   Empty/short pages: {sum(1 for p in data if len(p.get('body', '')) <= 100)}")

# Content length distribution
lengths = [len(p.get('body', '')) for p in data if p.get('body')]
if lengths:
    print(f"\n📏 CONTENT LENGTH:")
    print(f"   Average: {int(sum(lengths)/len(lengths)):,} chars")
    print(f"   Minimum: {min(lengths):,} chars")
    print(f"   Maximum: {max(lengths):,} chars")

# Content distribution by size
print(f"\n📦 CONTENT DISTRIBUTION:")
short = sum(1 for l in lengths if l <= 500)
medium = sum(1 for l in lengths if 501 <= l <= 2000)
long_content = sum(1 for l in lengths if 2001 <= l <= 5000)
very_long = sum(1 for l in lengths if l > 5000)

print(f"   Short (0-500 chars): {short} pages")
print(f"   Medium (501-2K chars): {medium} pages")
print(f"   Long (2K-5K chars): {long_content} pages")
print(f"   Very Long (5K+ chars): {very_long} pages")

# URL analysis
urls = [p['url'] for p in data]
unique_domains = set(url.split('/')[2] for url in urls)
print(f"\n🔗 URL ANALYSIS:")
print(f"   Unique domains: {len(unique_domains)}")
print(f"   Domains: {', '.join(unique_domains)}")

# Challenge type detection
challenge_keywords = {
    'Stellar 1-Step': sum(1 for p in data if '1-step' in p.get('title', '').lower() or '1 step' in p.get('title', '').lower()),
    'Stellar 2-Step': sum(1 for p in data if '2-step' in p.get('title', '').lower() or '2 step' in p.get('title', '').lower()),
    'Stellar Lite': sum(1 for p in data if 'lite' in p.get('title', '').lower()),
    'Stellar Instant': sum(1 for p in data if 'instant' in p.get('title', '').lower()),
    'Trading Rules': sum(1 for p in data if 'rule' in p.get('title', '').lower() or 'prohibited' in p.get('title', '').lower()),
}

print(f"\n🎯 CONTENT TYPE DETECTION:")
for keyword, count in challenge_keywords.items():
    if count > 0:
        print(f"   {keyword}: {count} pages")

# Rule keywords in content
rule_keywords = {
    'daily loss': sum(1 for p in data if 'daily loss' in p.get('body', '').lower()),
    'max drawdown': sum(1 for p in data if 'drawdown' in p.get('body', '').lower()),
    'profit target': sum(1 for p in data if 'profit target' in p.get('body', '').lower()),
    'prohibited': sum(1 for p in data if 'prohibited' in p.get('body', '').lower()),
    'copy trading': sum(1 for p in data if 'copy trading' in p.get('body', '').lower()),
    'leverage': sum(1 for p in data if 'leverage' in p.get('body', '').lower()),
}

print(f"\n🔍 RULE KEYWORD COVERAGE:")
for keyword, count in rule_keywords.items():
    print(f"   '{keyword}': found in {count} pages ({count/len(data)*100:.1f}%)")

# Sample pages
print(f"\n📄 SAMPLE PAGES (first 5):")
for i, page in enumerate(data[:5], 1):
    print(f"\n   {i}. {page['title'][:60]}")
    print(f"      URL: {page['url']}")
    print(f"      Length: {len(page.get('body', '')):,} chars")
    preview = page.get('body', '')[:150].replace('\n', ' ')
    print(f"      Preview: {preview}...")

# Quality grade
print(f"\n{'='*70}")
print("🎓 QUALITY GRADE")
print("="*70)

score = 0
max_score = 100

# Scoring criteria
if len(data) >= 200:
    score += 20
    print("✓ Volume: 20/20 (200+ pages scraped)")
elif len(data) >= 100:
    score += 15
    print("⚠ Volume: 15/20 (100-199 pages)")
else:
    score += 10
    print("✗ Volume: 10/20 (<100 pages)")

empty_ratio = sum(1 for p in data if len(p.get('body', '')) <= 100) / len(data)
if empty_ratio < 0.05:
    score += 20
    print("✓ Content Quality: 20/20 (<5% empty pages)")
elif empty_ratio < 0.15:
    score += 15
    print("⚠ Content Quality: 15/20 (5-15% empty pages)")
else:
    score += 10
    print("✗ Content Quality: 10/20 (>15% empty pages)")

avg_length = sum(lengths) / len(lengths) if lengths else 0
if avg_length > 2000:
    score += 20
    print("✓ Content Depth: 20/20 (avg 2000+ chars)")
elif avg_length > 1000:
    score += 15
    print("⚠ Content Depth: 15/20 (avg 1000-2000 chars)")
else:
    score += 10
    print("✗ Content Depth: 10/20 (avg <1000 chars)")

rule_coverage = sum(1 for v in rule_keywords.values() if v > 10)
if rule_coverage >= 5:
    score += 20
    print("✓ Rule Coverage: 20/20 (5+ rule types found)")
elif rule_coverage >= 3:
    score += 15
    print("⚠ Rule Coverage: 15/20 (3-4 rule types found)")
else:
    score += 10
    print("✗ Rule Coverage: 10/20 (<3 rule types found)")

challenge_coverage = sum(1 for v in challenge_keywords.values() if v > 0)
if challenge_coverage >= 4:
    score += 20
    print("✓ Challenge Coverage: 20/20 (4+ challenge types)")
elif challenge_coverage >= 2:
    score += 15
    print("⚠ Challenge Coverage: 15/20 (2-3 challenge types)")
else:
    score += 10
    print("✗ Challenge Coverage: 10/20 (<2 challenge types)")

print(f"\n{'='*70}")
print(f"FINAL SCORE: {score}/100")

if score >= 90:
    grade = "A+ (Excellent)"
elif score >= 80:
    grade = "A (Very Good)"
elif score >= 70:
    grade = "B (Good)"
elif score >= 60:
    grade = "C (Average)"
else:
    grade = "D (Needs Improvement)"

print(f"GRADE: {grade}")
print("="*70)
