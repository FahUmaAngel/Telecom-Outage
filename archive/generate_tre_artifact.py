import os

artifact_path = r'C:\Users\Umakue\.gemini\antigravity\brain\990f6b8a-be55-4e60-8f9f-3154b6261fdd\tre_missing_coords.md'
input_path = r'd:\94 FAH works\Telecom-Outage\tre_missing.txt'

try:
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    with open(artifact_path, 'w', encoding='utf-8') as out:
        out.write("# Tre Incidents Missing Coordinates\n\n")
        out.write("Total incidents: **171**\n\n")
        out.write("| Incident ID | Location | Latitude | Longitude | Place (Plus Code) |\n")
        out.write("|---|---|---|---|---|\n")
        
        for line in lines[1:]: # Skip first count line
            if not line.strip(): continue
            parts = line.split('|')
            inc_id = parts[0].replace('- ID:', '').strip()
            loc = parts[1].replace('Location:', '').strip()
            out.write(f"| {inc_id} | {loc} | NULL | NULL | NULL |\n")
            
    print("Markdown file generated successfully.")
except Exception as e:
    print(f"Error generating markdown: {e}")
