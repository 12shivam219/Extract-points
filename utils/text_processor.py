import re

class TextProcessor:
    def __init__(self):
        self.bullet_pattern = r'[•\-]\s*(.*)'
        self.heading_pattern = r'^[A-Za-z].*$'

    def is_heading(self, line):
        """Check if a line is a heading."""
        line = line.strip()
        return bool(re.match(self.heading_pattern, line)) and not line.startswith('•') and not line.startswith('-')

    def is_bullet_point(self, line):
        """Check if a line is a bullet point."""
        return bool(re.match(self.bullet_pattern, line.strip()))

    def extract_bullet_point(self, line):
        """Extract the content of a bullet point."""
        match = re.match(self.bullet_pattern, line.strip())
        return match.group(1) if match else None

    def process_text(self, text, points_per_cycle):
        """Process the input text and extract points in cycles."""
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        if points_per_cycle < 1:
            raise ValueError("Points per cycle must be at least 1")

        # Split text into lines and process
        lines = text.split('\n')
        current_heading = None
        structured_content = {}

        # First pass: organize content
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if self.is_heading(line):
                current_heading = line
                structured_content[current_heading] = []
            elif self.is_bullet_point(line) and current_heading:
                point = self.extract_bullet_point(line)
                if point:
                    structured_content[current_heading].append(point)

        if not structured_content:
            raise ValueError("No valid headings or bullet points found in the input text")

        # Second pass: extract points in cycles
        result = []
        max_points = max(len(points) for points in structured_content.values())
        current_cycle = 0

        while current_cycle * points_per_cycle < max_points:
            start_idx = current_cycle * points_per_cycle
            end_idx = start_idx + points_per_cycle

            cycle_content = [f"\nCycle {current_cycle + 1}:"]
            for heading, points in structured_content.items():
                cycle_content.append(f"\n{heading}")
                cycle_points = points[start_idx:end_idx]
                for point in cycle_points:
                    cycle_content.append(f"• {point}")

            result.extend(cycle_content)
            current_cycle += 1

        return "\n".join(result)