from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from copy import deepcopy
import io
import re

class ResumeInjector:
    """Handles injecting extracted points into resume templates with bookmarks."""
    
    def __init__(self):
        # Map section headings to resume bookmarks
        self.heading_to_bookmark = {
            'kpmg': 'KPMG_Responsibilities',
            'cvs': 'CVS_Responsibilities',
            'harland': 'Harland_Responsibilities',
            'first citizen': 'FirstCitizensBank_Responsibilities',
            'first citizens': 'FirstCitizensBank_Responsibilities',
        }
    
    def extract_points_by_heading(self, processed_text):
        """
        Extract points from processed text organized by cycle.
        Works with Cycle format:
        Cycle 1: / • Point 1
        Cycle 2: / • Point 2
        etc.
        
        Returns: points_by_cycle dict like {1: [points], 2: [points], ...}
        """
        points_by_cycle = {}
        current_cycle = None
        all_points = []  # Track all points found
        
        lines = processed_text.split('\n')
        
        print(f"\n[DEBUG] Total lines: {len(lines)}")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for cycle header (Cycle 1:, Cycle 2:, etc.)
            cycle_match = re.match(r'Cycle\s+(\d+):', line, re.IGNORECASE)
            if cycle_match:
                current_cycle = int(cycle_match.group(1))
                print(f"[DEBUG] Found Cycle {current_cycle}")
                if current_cycle not in points_by_cycle:
                    points_by_cycle[current_cycle] = []
                continue
            
            # Extract bullet points OR long lines (which are likely points without bullets)
            point_text = None
            
            # Check for various bullet formats
            if line.startswith('•'):
                point_text = re.sub(r'^•\s*', '', line).strip()
                print(f"[DEBUG] Found bullet point (•) in Cycle {current_cycle}: '{point_text}'")
            
            elif line.startswith('-') and not line.startswith('--'):
                point_text = re.sub(r'^-\s*', '', line).strip()
                print(f"[DEBUG] Found dash point (-) in Cycle {current_cycle}: '{point_text}'")
            
            elif line.startswith('*') and not line.startswith('**'):
                point_text = re.sub(r'^\*\s*', '', line).strip()
                print(f"[DEBUG] Found asterisk point (*) in Cycle {current_cycle}: '{point_text}'")
            
            elif line.startswith('+'):
                point_text = re.sub(r'^\+\s*', '', line).strip()
                print(f"[DEBUG] Found plus point (+) in Cycle {current_cycle}: '{point_text}'")
            
            elif re.match(r'^\d+\.', line):
                point_text = re.sub(r'^\d+\.\s*', '', line).strip()
                print(f"[DEBUG] Found numbered point in Cycle {current_cycle}: '{point_text}'")
            
            # Fallback: If line is long (30+ chars) and meaningful, treat as point
            elif len(line) >= 30 and not line.startswith('=') and not line.startswith('_') and not line.startswith('Cycle'):
                point_text = line
                print(f"[DEBUG] Found potential point (no bullet, long line) in Cycle {current_cycle}: '{line[:50]}...'")
            
            # Add point if found
            if point_text:
                all_points.append(point_text)
                if current_cycle is not None:
                    points_by_cycle[current_cycle].append(point_text)
        
        print(f"[DEBUG] Total points found: {len(all_points)}")
        print(f"[DEBUG] Points by cycle: {[(cycle, len(points)) for cycle, points in sorted(points_by_cycle.items())]}")
        
        return points_by_cycle, all_points
    
    def find_bookmark_paragraph(self, doc, bookmark_name):
        """Find the paragraph that contains a bookmark."""
        # Search all paragraphs for the bookmark
        for para in doc.paragraphs:
            # Check paragraph XML directly
            if bookmark_name in para._element.xml:
                return para
        
        # If not found in paragraphs, check all elements more thoroughly
        from docx.oxml import OxmlElement as OE
        for element in doc.element.iter():
            if bookmark_name in element.tag or (hasattr(element, 'attrib') and any(bookmark_name in str(v) for v in element.attrib.values())):
                # Find parent paragraph
                parent = element.getparent()
                while parent is not None:
                    if 'p' in parent.tag:  # paragraph element
                        # Find the paragraph object
                        for para in doc.paragraphs:
                            if para._element == parent:
                                return para
                    parent = parent.getparent()
        
        return None
    
    def copy_list_formatting(self, source_para, target_para):
        """
        Copy list/bullet formatting from source paragraph to target paragraph.
        This ensures bullets are properly applied.
        """
        try:
            source_pPr = source_para._element.get_or_add_pPr()
            target_pPr = target_para._element.get_or_add_pPr()
            
            # Look for numPr (numbering properties) element
            source_numPr = source_pPr.find(qn('w:numPr'))
            
            if source_numPr is not None:
                # Deep copy the numbering properties
                target_numPr = target_pPr.find(qn('w:numPr'))
                if target_numPr is not None:
                    target_pPr.remove(target_numPr)
                
                # Copy the numPr element
                new_numPr = deepcopy(source_numPr)
                target_pPr.append(new_numPr)
                print(f"[DEBUG] Successfully copied list formatting (numPr) to new paragraph")
            else:
                print(f"[DEBUG] Source paragraph has no list formatting (numPr) to copy")
                
        except Exception as e:
            print(f"[DEBUG] Could not copy list formatting: {str(e)}")
    
    def inject_points_into_resume(self, resume_bytes, processed_text):
        """
        Inject extracted points into resume at bookmarks by cycle order.
        Maps cycles to companies in order:
        - Cycle 1 → KPMG (1st company)
        - Cycle 2 → CVS (2nd company)
        - Cycle 3 → Harland (3rd company)
        - Cycle 4 → First Citizens Bank (4th company)
        
        Args:
            resume_bytes: BytesIO object of the resume template
            processed_text: Processed text organized by cycles
            
        Returns:
            BytesIO object with updated resume, injection details
        """
        try:
            doc = Document(resume_bytes)
            points_by_cycle, all_points = self.extract_points_by_heading(processed_text)
            
            if not all_points:
                raise ValueError("No points found in processed text. Check the format.")
            
            # Get all available bookmarks in the resume
            available_bookmarks = self.get_available_bookmarks(resume_bytes)
            
            if not available_bookmarks:
                raise ValueError("No bookmarks found in resume template. Please add bookmarks first.")
            
            # Map cycles to bookmarks in order
            cycle_to_bookmark = {}
            sorted_bookmarks = sorted(available_bookmarks)  # Ensure consistent order
            
            # Company order mapping
            company_order = [
                'KPMG_Responsibilities',
                'CVS_Responsibilities',
                'Harland_Responsibilities',
                'FirstCitizensBank_Responsibilities'
            ]
            
            # Use predefined order if available
            for idx, company in enumerate(company_order):
                if company in available_bookmarks:
                    cycle_to_bookmark[idx + 1] = company  # Cycle 1, 2, 3, 4...
            
            print(f"[DEBUG] Cycle to bookmark mapping: {cycle_to_bookmark}")
            print(f"[DEBUG] Points by cycle: {points_by_cycle}")
            
            # Track injections for feedback
            injections = {}
            
            # Inject points for each cycle into its corresponding bookmark
            for cycle_num in sorted(points_by_cycle.keys()):
                if cycle_num not in cycle_to_bookmark:
                    print(f"[DEBUG] Warning: Cycle {cycle_num} has no corresponding company bookmark")
                    continue
                
                bookmark_name = cycle_to_bookmark[cycle_num]
                cycle_points = points_by_cycle[cycle_num]
                
                if not cycle_points:
                    print(f"[DEBUG] Cycle {cycle_num} has no points to inject")
                    continue
                
                print(f"[DEBUG] Injecting Cycle {cycle_num} points into {bookmark_name}")
                
                bookmark_para = self.find_bookmark_paragraph(doc, bookmark_name)
                
                if not bookmark_para:
                    # Bookmark not found, try to insert after the company section heading
                    company_section_name = bookmark_name.replace('_Responsibilities', '')
                    found = False
                    for para_idx, para in enumerate(doc.paragraphs):
                        if 'Responsibilities' in para.text and company_section_name in para.text:
                            bookmark_para = doc.paragraphs[para_idx + 1] if para_idx + 1 < len(doc.paragraphs) else para
                            found = True
                            print(f"[DEBUG] Found {company_section_name} section at paragraph {para_idx}")
                            break
                    
                    if not found:
                        # Try any responsibility section
                        for para_idx, para in enumerate(doc.paragraphs):
                            if 'Responsibilities' in para.text:
                                bookmark_para = doc.paragraphs[min(para_idx + 2, len(doc.paragraphs) - 1)]
                                found = True
                                break
                
                if bookmark_para:
                    reference_para = bookmark_para
                    
                    # Get the parent element and insertion point
                    parent = reference_para._element.getparent()
                    ref_index = None
                    try:
                        ref_index = list(parent).index(reference_para._element)
                    except ValueError:
                        # If not found in parent, it might be in a different structure
                        # Find the closest preceding paragraph
                        for idx, para in enumerate(doc.paragraphs):
                            if para._element == reference_para._element:
                                ref_index = idx
                                break
                    
                    if ref_index is None:
                        print(f"[DEBUG] Warning: Could not find reference paragraph, appending to end")
                        ref_index = len(list(parent)) - 1
                    
                    # Add points for this cycle
                    for i, point_text in enumerate(cycle_points):
                        # Get the reference style - use the same style as reference
                        ref_style_name = reference_para.style.name if reference_para.style else 'Normal'
                        
                        # Add new paragraph directly to the document
                        new_para = doc.add_paragraph(point_text, style=ref_style_name)
                        
                        # Copy paragraph formatting from reference
                        ref_pformat = reference_para.paragraph_format
                        new_pformat = new_para.paragraph_format
                        
                        new_pformat.left_indent = ref_pformat.left_indent
                        new_pformat.first_line_indent = ref_pformat.first_line_indent
                        new_pformat.space_before = ref_pformat.space_before
                        new_pformat.space_after = ref_pformat.space_after
                        if ref_pformat.line_spacing:
                            new_pformat.line_spacing = ref_pformat.line_spacing
                        
                        # Copy font formatting from reference
                        if reference_para.runs and len(reference_para.runs) > 0:
                            ref_run = reference_para.runs[0]
                            for run in new_para.runs:
                                if ref_run.font.name:
                                    run.font.name = ref_run.font.name
                                if ref_run.font.size:
                                    run.font.size = ref_run.font.size
                                if ref_run.font.bold:
                                    run.font.bold = ref_run.font.bold
                                if ref_run.font.italic:
                                    run.font.italic = ref_run.font.italic
                                if ref_run.font.color.rgb:
                                    run.font.color.rgb = ref_run.font.color.rgb
                        
                        # CRITICAL: Copy list/bullet formatting from reference
                        self.copy_list_formatting(reference_para, new_para)
                        
                        # Now move the paragraph to the correct position (after reference)
                        new_parent = new_para._element.getparent()
                        
                        # Remove from the end where it was added
                        new_parent.remove(new_para._element)
                        
                        # Insert at the correct position in the parent
                        try:
                            ref_index = list(parent).index(reference_para._element)
                            parent.insert(ref_index + 1 + i, new_para._element)
                        except (ValueError, IndexError) as e:
                            print(f"[DEBUG] Warning: Could not insert at position, appending instead: {str(e)}")
                            parent.append(new_para._element)
                    
                    injections[bookmark_name] = len(cycle_points)
                    print(f"[DEBUG] Successfully injected {len(cycle_points)} points into {bookmark_name}")
            
            if not injections:
                raise ValueError("Failed to inject points. No valid insertion points found.")
            
            # Save to BytesIO
            output = io.BytesIO()
            doc.save(output)
            output.seek(0)
            
            return output, injections
            
        except Exception as e:
            raise Exception(f"Error injecting points into resume: {str(e)}")
    
    def get_available_bookmarks(self, resume_bytes):
        """Get list of available bookmarks in resume template."""
        try:
            doc = Document(resume_bytes)
            bookmarks = set()
            
            # Method 1: Check paragraph XML
            for para in doc.paragraphs:
                if para._element.xml:
                    # Look for bookmarkStart elements
                    matches = re.findall(r'w:name="([^"]*)"', para._element.xml)
                    bookmarks.update(matches)
            
            # Method 2: Check in all runs
            for para in doc.paragraphs:
                for run in para.runs:
                    if run._element.xml:
                        matches = re.findall(r'w:name="([^"]*)"', run._element.xml)
                        bookmarks.update(matches)
            
            # Method 3: Deep search in all elements
            from docx.oxml import parse_xml
            for element in doc.element.iter():
                tag = element.tag
                if 'bookmark' in tag.lower():
                    name = element.get(qn('w:name'))
                    if name:
                        bookmarks.add(name)
            
            # If no bookmarks found, return default ones for this template
            if not bookmarks:
                # Default bookmarks for the Lead Engineer template
                bookmarks = {
                    'KPMG_Responsibilities',
                    'CVS_Responsibilities', 
                    'Harland_Responsibilities',
                    'FirstCitizensBank_Responsibilities'
                }
            
            return list(bookmarks)
        except Exception as e:
            # Return default bookmarks if detection fails
            return [
                'KPMG_Responsibilities',
                'CVS_Responsibilities',
                'Harland_Responsibilities', 
                'FirstCitizensBank_Responsibilities'
            ]
