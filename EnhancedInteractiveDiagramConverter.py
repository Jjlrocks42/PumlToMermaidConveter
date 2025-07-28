import hashlib

from InteractiveDiagramConverter import InteractiveDiagramConverter

class EnhancedInteractiveDiagramConverter(InteractiveDiagramConverter):
    def __init__(self):
        super().__init__()

    def hash_to_color(self, text, palette):
        """Hash a text to a color in the given palette."""
        hashed_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return palette[hashed_value % len(palette)]

    def get_section_colors(self, class_name: str, class_type: str) -> tuple:
        """Determine colors based on package hierarchy and class type."""
        section = self.get_section_type(class_name)
        palette = self.get_color_palette()

        # Assign colors based on section
        if section == 'common':
            return self.hash_to_color(class_name, palette[1])
        elif section == 'config':
            return self.hash_to_color(class_name, palette[2])
        elif section == 'customer_facing':
            return self.hash_to_color(class_name, palette[3])
        elif section == 'field_staff':
            return self.hash_to_color(class_name, palette[4])
        else:
            return self.hash_to_color(class_name, palette['default'])

    def calculate_position(self, total_classes: int) -> dict:
        """Calculate positions for all classes across sections."""
        sections = {
            'field_staff': [],
            'customer_facing': [],
            'common': [],
            'config': [],
            'other': []
        }

        for class_name, _ in self.classes.items():
            section = self.get_section_type(class_name)
            sections[section].append(class_name)

        positions = {}
        section_x = {
            'field_staff': 100,
            'common': 400,
            'customer_facing': 700,
            'config': 250,
            'other': 550
        }

        spacing = 150

        for section, x in section_x.items():
            for index, class_name in enumerate(sections[section]):
                y = 100 + (index * spacing)
                positions[class_name] = {'x': x, 'y': y}

        return positions

# Usage Example
def main():
    puml_code = """class za.co.ist.poa.common.ExpressionAttributes$COMPARATOR
class za.co.ist.poa.common.IncidentAttributes
class za.co.ist.poa.configs.client.SMSGatewayClient
class za.co.ist.poa.configs.client.SMSGatewayClientConfig
"""

    converter = EnhancedInteractiveDiagramConverter()
    diagram_data = converter.convert_to_interactive(puml_code)

    print(json.dumps(diagram_data, indent=4))

if __name__ == "__main__":
    main()