import re

class TextProcessor:
    def __init__(self):
        # Updated patterns to handle both bullet points and numbered lists
        self.bullet_pattern = r'(?:•|\-|\d+\.)\s*(.*)'
        self.heading_pattern = r'^(?!(?:•|\-|\d+\.))[A-Za-z].*$'

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
        current_heading = None
        structured_content = {}

        print("\nFirst pass - organizing content:")  # Debug print
        # First pass: organize content
        for line in lines:
            print(f"Processing line: {line}")  # Debug print

            if self.is_heading(line):
                current_heading = line
                structured_content[current_heading] = []
                print(f"Found heading: {current_heading}")  # Debug print
            elif self.is_bullet_point(line) and current_heading:
                point = self.extract_bullet_point(line)
                if point:
                    structured_content[current_heading].append(point)
                    print(f"Added point: {point} to heading: {current_heading}")  # Debug print

        if not structured_content:
            print("Error: No valid content found")  # Debug print
            raise ValueError("No valid headings or bullet points found in the input text")

        print("\nSecond pass - creating cycles:")  # Debug print
        # Second pass: extract points in cycles
        result = []
        max_points = max(len(points) for points in structured_content.values())
        current_cycle = 0

        while current_cycle * points_per_cycle < max_points:
            start_idx = current_cycle * points_per_cycle
            end_idx = start_idx + points_per_cycle

            print(f"\nProcessing Cycle {current_cycle + 1}")  # Debug print

            cycle_content = [f"Cycle {current_cycle + 1}:"]
            for heading, points in structured_content.items():
                cycle_content.append(f"\n{heading}")
                cycle_points = points[start_idx:end_idx]
                for point in cycle_points:
                    cycle_content.append(f"• {point}")
                print(f"Added {len(cycle_points)} points for heading: {heading}")  # Debug print

            result.extend(cycle_content)
            current_cycle += 1

        final_text = "\n".join(result)
        print(f"\nFinal processed text:\n{final_text}")  # Debug print
        return final_text