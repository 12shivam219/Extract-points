import re

class TextProcessor:
    def __init__(self):
        # More flexible patterns to handle various formats
        self.bullet_pattern = r'(?:•|\-|\*|\+|\d+\.|\([a-z0-9]\))\s*(.*)'
        self.heading_pattern = r'^(?!(?:•|\-|\*|\+|\d+\.|\([a-z0-9]\)))[A-Za-z0-9].*$'

    def is_heading(self, line):
        """Check if a line is a heading."""
        line = line.strip()
        # Add print for debugging
        print(f"Checking if heading: {line}")
        return bool(re.match(self.heading_pattern, line))

    def is_bullet_point(self, line):
        """Check if a line is a bullet point."""
        line = line.strip()
        # Add print for debugging
        print(f"Checking if bullet point: {line}")
        return bool(re.match(self.bullet_pattern, line))

    def extract_bullet_point(self, line):
        """Extract the content of a bullet point."""
        match = re.match(self.bullet_pattern, line.strip())
        if match:
            # Add print for debugging
            print(f"Extracted bullet point: {match.group(1)}")
            return match.group(1)
        return None

    def process_text(self, text, points_per_cycle):
        """Process the input text and extract points in cycles."""
        print("\nProcessing text...")  # Debug print

        if not text or not text.strip():
            print("Error: Empty input text")  # Debug print
            raise ValueError("Input text cannot be empty")

        if points_per_cycle < 1:
            print("Error: Invalid points per cycle")  # Debug print
            raise ValueError("Points per cycle must be at least 1")

        # Split text into lines and process
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        if not lines:
            print("Error: No valid lines found after splitting")
            raise ValueError("No valid text content found after splitting")
            
        # Ensure we have at least one heading by setting a default if none is found
        has_heading = any(self.is_heading(line) for line in lines)
        if not has_heading:
            print("Warning: No explicit headings found, treating first line as heading")
            
        current_heading = None
        structured_content = {}

        print("\nFirst pass - organizing content:")  # Debug print
        # First pass: organize content
        for i, line in enumerate(lines):
            print(f"Processing line {i+1}: {line}")  # Debug print

            # If no heading is found and this is the first line, treat it as a heading
            if current_heading is None and i == 0 and not has_heading:
                current_heading = line
                structured_content[current_heading] = []
                print(f"Using first line as heading: {current_heading}")
            elif self.is_heading(line):
                current_heading = line
                structured_content[current_heading] = []
                print(f"Found heading: {current_heading}")  # Debug print
            elif current_heading is not None:  # If we have a heading, treat any non-heading as a potential bullet point
                # Check if it's a bullet point
                if self.is_bullet_point(line):
                    point = self.extract_bullet_point(line)
                    if point:
                        structured_content[current_heading].append(point)
                        print(f"Added bullet point: {point} to heading: {current_heading}")
                else:
                    # If it's not recognized as a bullet point, add it as a plain point
                    structured_content[current_heading].append(line)
                    print(f"Added plain text as point: {line} to heading: {current_heading}")
            else:
                print(f"Warning: Line ignored, no current heading: {line}")

        if not structured_content:
            print("Error: No valid content found")  # Debug print
            raise ValueError("""No valid headings or bullet points found in the input text. 
            
Format example:
Heading 1
• Point 1
• Point 2

Heading 2
• Item A
• Item B""")
            
        # Log the structured content for debugging
        print("\nStructured content:")
        for heading, points in structured_content.items():
            print(f"Heading: {heading}")
            for point in points:
                print(f"  • {point}")

        print("\nSecond pass - creating cycles:")  # Debug print
        # Second pass: extract points in cycles
        result = []
        
        # Get the maximum number of points across all headings
        max_points = max(len(points) for points in structured_content.values()) if structured_content else 0
        
        if max_points == 0:
            print("Warning: No points found under headings")
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

            print(f"\nProcessing Cycle {current_cycle + 1}")  # Debug print

            cycle_content = [f"Cycle {current_cycle + 1}:"]
            for heading, points in structured_content.items():
                cycle_content.append(f"\n{heading}")
                cycle_points = points[start_idx:min(end_idx, len(points))]  # Ensure we don't go out of bounds
                for point in cycle_points:
                    cycle_content.append(f"• {point}")
                print(f"Added {len(cycle_points)} points for heading: {heading}")  # Debug print

            result.extend(cycle_content)
            current_cycle += 1

        if not result:
            print("Error: No result generated")
            raise ValueError("Failed to generate output. Please check your input format.")

        final_text = "\n".join(result)
        print(f"\nFinal processed text:\n{final_text}")  # Debug print
        return final_text