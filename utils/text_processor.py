import re

class TextProcessor:
    def __init__(self):
        # More flexible patterns to handle various formats
        self.bullet_pattern = r'(?:•|\-|\*|\+|\d+\.|\([a-z0-9]\))\s*(.*)'
        self.heading_pattern = r'^(?!(?:•|\-|\*|\+|\d+\.|\([a-z0-9]\)))[A-Za-z0-9].*$'

    def is_heading(self, line):
        """Check if a line is a heading."""
        line = line.strip()
        return bool(re.match(self.heading_pattern, line))

    def is_bullet_point(self, line):
        """Check if a line is a bullet point."""
        line = line.strip()
        return bool(re.match(self.bullet_pattern, line))

    def extract_bullet_point(self, line):
        """Extract the content of a bullet point."""
        match = re.match(self.bullet_pattern, line.strip())
        if match:
            return match.group(1)
        return None

    def process_text(self, text, points_per_cycle):
        """Process the input text and extract points in cycles."""
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        if points_per_cycle < 1:
            raise ValueError("Points per cycle must be at least 1")

        # Split text into lines and process
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            raise ValueError("No valid text content found after splitting")
            
        # Ensure we have at least one heading by setting a default if none is found
        has_heading = any(self.is_heading(line) for line in lines)
        if not has_heading:
            pass  # Will treat first line as heading below
            
        current_heading = None
        structured_content = {}

        # First pass: organize content
        for i, line in enumerate(lines):
            # Skip lines that are only underscores
            if line.replace('_', '').strip() == '':
                continue
            
            # If no heading is found and this is the first line, treat it as a heading
            if current_heading is None and i == 0 and not has_heading:
                current_heading = line
                structured_content[current_heading] = []
            elif self.is_heading(line):
                current_heading = line
                structured_content[current_heading] = []
            elif current_heading is not None:  # If we have a heading, treat any non-heading as a potential bullet point
                # Check if it's a bullet point
                if self.is_bullet_point(line):
                    point = self.extract_bullet_point(line)
                    if point:
                        structured_content[current_heading].append(point)
                else:
                    # If it's not recognized as a bullet point, add it as a plain point
                    structured_content[current_heading].append(line)

        if not structured_content:
            raise ValueError("""No valid headings or bullet points found in the input text. 
            
Format example:
Heading 1
• Point 1
• Point 2

Heading 2
• Item A
• Item B""")
            
        # Second pass: extract points in cycles
        result = []
        
        # Get the maximum number of points across all headings
        max_points = max(len(points) for points in structured_content.values()) if structured_content else 0
        
        if max_points == 0:
            raise ValueError("""No points found under any headings. Please check your input format.
            
Correct format example:
Heading 1
• Point 1
• Point 2

Heading 2
• Item A
• Item B
            
You can use •, -, *, +, or numbers (1. 2.) for bullet points.""")
            
        current_cycle = 0

        while current_cycle * points_per_cycle < max_points:
            start_idx = current_cycle * points_per_cycle
            end_idx = start_idx + points_per_cycle

            cycle_content = [f"Cycle {current_cycle + 1}:"]
            
            # Organize points by heading within each cycle
            for heading, points in structured_content.items():
                heading_points = points[start_idx:min(end_idx, len(points))]
                if heading_points:  # Only add points for this cycle
                    for point in heading_points:
                        cycle_content.append(point)

            result.extend(cycle_content)
            current_cycle += 1

        if not result:
            raise ValueError("Failed to generate output. Please check your input format.")

        final_text = "\n".join(result)
        return final_text