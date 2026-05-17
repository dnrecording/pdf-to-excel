"""GUI application for PDF to Excel converter."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from typing import Optional

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

from .extractor import OCRExtractor
from .writer import ExcelWriter
from .exceptions import PDFToExcelError, FileValidationError
from .page_selector import parse_page_selection, get_pdf_page_count, validate_page_selection


# Nord color scheme
NORD_COLORS = {
    'bg': '#2E3440',           # Dark background
    'bg_lighter': '#3B4252',   # Lighter background
    'bg_highlight': '#434C5E', # Highlight background
    'fg': '#ECEFF4',           # Light foreground text
    'fg_dim': '#D8DEE9',       # Dimmed text
    'accent': '#88C0D0',       # Cyan accent
    'accent_green': '#A3BE8C', # Green
    'accent_yellow': '#EBCB8B',# Yellow
    'accent_red': '#BF616A',   # Red
    'accent_blue': '#81A1C1',  # Blue
    'frost': '#8FBCBB',        # Frost color
}


class ModernButton(tk.Canvas):
    """Modern button with hover effects."""

    def __init__(self, parent, text, command, width=200, height=40,
                 bg=NORD_COLORS['accent'], hover_bg=NORD_COLORS['frost'],
                 fg=NORD_COLORS['bg'], disabled_bg='#4C566A', **kwargs):
        super().__init__(parent, width=width, height=height,
                        bg=NORD_COLORS['bg'], highlightthickness=0, **kwargs)

        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.bg_color = bg
        self.hover_bg = hover_bg
        self.fg_color = fg
        self.disabled_bg = disabled_bg
        self.is_disabled = False
        self.is_hovered = False

        self._draw()
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)

    def _draw(self):
        """Draw the button."""
        self.delete('all')

        if self.is_disabled:
            bg = self.disabled_bg
        elif self.is_hovered:
            bg = self.hover_bg
        else:
            bg = self.bg_color

        # Rounded rectangle
        radius = 8
        self.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, fill=bg, outline=bg)
        self.create_arc(self.width-radius*2, 0, self.width, radius*2, start=0, extent=90, fill=bg, outline=bg)
        self.create_arc(0, self.height-radius*2, radius*2, self.height, start=180, extent=90, fill=bg, outline=bg)
        self.create_arc(self.width-radius*2, self.height-radius*2, self.width, self.height, start=270, extent=90, fill=bg, outline=bg)

        self.create_rectangle(radius, 0, self.width-radius, self.height, fill=bg, outline=bg)
        self.create_rectangle(0, radius, self.width, self.height-radius, fill=bg, outline=bg)

        # Text
        self.create_text(self.width/2, self.height/2, text=self.text,
                        fill=self.fg_color, font=('SF Pro', 13, 'bold'))

    def _on_enter(self, event):
        """Handle mouse enter."""
        if not self.is_disabled:
            self.is_hovered = True
            self._draw()

    def _on_leave(self, event):
        """Handle mouse leave."""
        self.is_hovered = False
        self._draw()

    def _on_click(self, event):
        """Handle click."""
        if not self.is_disabled and self.command:
            self.command()

    def set_state(self, state):
        """Set button state."""
        self.is_disabled = (state == 'disabled')
        self._draw()

    def set_text(self, text):
        """Update button text."""
        self.text = text
        self._draw()


class PDFToExcelGUI:
    """GUI application for converting PDFs to Excel."""

    def __init__(self, root: tk.Tk):
        """Initialize the GUI."""
        self.root = root
        self.root.title("PDF to Excel Converter")
        self.root.geometry("700x650")
        self.root.resizable(False, False)
        self.root.configure(bg=NORD_COLORS['bg'])

        # Set window icon (using default for now)
        try:
            # Try to set a default icon
            self.root.iconphoto(True, tk.PhotoImage(data=self._get_icon_data()))
        except:
            pass  # Skip if icon fails

        # Variables
        self.pdf_path: Optional[str] = None
        self.is_converting = False
        self.is_browsing = False  # Flag to prevent multiple browse dialogs

        # Configure ttk style
        self._setup_style()

        # Setup UI
        self._setup_ui()

    def _get_icon_data(self) -> str:
        """Return base64 PNG icon data."""
        # Simple PDF icon as base64 PNG (16x16)
        return """
        iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlz
        AAALEwAACxMBAJqcGAAAAWZJREFUOI2Nkz1Lw1AUhp+bpGma1NYPKjgITqKDi4uCODg4ufsH/AH+
        AP+Ag4ODk4OTi4Og4KCCgmAXQaGIX7VKbWOS3iuNJqZpW3znnnPe89zDPecsYoxBURQMw0BRFBRF
        QVVVVFVFVVVUVUVRFDT9ixhjjJkxxhhjzBljjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhj
        jDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wx
        xhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYY
        Y4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4z5L38A8vZvPvJb
        lCcAAAAASUVORK5CYII=
        """

    def _setup_style(self) -> None:
        """Configure ttk widget styles."""
        style = ttk.Style()
        style.theme_use('default')

        # Configure colors
        style.configure('TFrame', background=NORD_COLORS['bg'])
        style.configure('TLabel',
                       background=NORD_COLORS['bg'],
                       foreground=NORD_COLORS['fg'],
                       font=('SF Pro', 11))
        style.configure('TLabelframe',
                       background=NORD_COLORS['bg'],
                       foreground=NORD_COLORS['fg'],
                       bordercolor=NORD_COLORS['bg_highlight'],
                       lightcolor=NORD_COLORS['bg_highlight'],
                       darkcolor=NORD_COLORS['bg_highlight'])
        style.configure('TLabelframe.Label',
                       background=NORD_COLORS['bg'],
                       foreground=NORD_COLORS['accent'],
                       font=('SF Pro', 12, 'bold'))

        # Combobox style
        style.configure('TCombobox',
                       fieldbackground=NORD_COLORS['bg_lighter'],
                       background=NORD_COLORS['bg_lighter'],
                       foreground=NORD_COLORS['fg'],
                       arrowcolor=NORD_COLORS['accent'],
                       bordercolor=NORD_COLORS['bg_highlight'],
                       lightcolor=NORD_COLORS['bg_highlight'],
                       darkcolor=NORD_COLORS['bg_highlight'])
        style.map('TCombobox',
                 fieldbackground=[('readonly', NORD_COLORS['bg_lighter'])],
                 selectbackground=[('readonly', NORD_COLORS['accent'])],
                 selectforeground=[('readonly', NORD_COLORS['bg'])])

        # Progressbar
        style.configure('TProgressbar',
                       background=NORD_COLORS['accent'],
                       troughcolor=NORD_COLORS['bg_lighter'],
                       bordercolor=NORD_COLORS['bg_highlight'],
                       lightcolor=NORD_COLORS['accent'],
                       darkcolor=NORD_COLORS['accent'])

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main frame with padding - centered
        main_frame = ttk.Frame(self.root, padding="40")
        main_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Title
        title_label = tk.Label(
            main_frame,
            text="📄 PDF to Excel Converter",
            font=("SF Pro", 28, "bold"),
            bg=NORD_COLORS['bg'],
            fg=NORD_COLORS['fg']
        )
        title_label.grid(row=0, column=0, pady=(0, 10))

        # Subtitle
        subtitle = tk.Label(
            main_frame,
            text="Convert scanned Thai/English PDFs to Excel",
            font=("SF Pro", 12),
            bg=NORD_COLORS['bg'],
            fg=NORD_COLORS['fg_dim']
        )
        subtitle.grid(row=1, column=0, pady=(0, 50))

        # Drop zone button
        self.drop_zone = tk.Canvas(
            main_frame,
            width=500,
            height=200,
            bg=NORD_COLORS['bg'],
            highlightthickness=0
        )
        self.drop_zone.grid(row=2, column=0, pady=(0, 20))

        # Store original colors for state management
        self.drop_zone_bg = NORD_COLORS['bg_lighter']
        self.drop_zone_border = NORD_COLORS['bg_highlight']
        self.drop_zone_icon = "📁"
        # Show drag & drop hint if available
        if HAS_DND and isinstance(self.root, TkinterDnD.Tk):
            self.drop_zone_text = "Click to select or drag & drop PDF"
        else:
            self.drop_zone_text = "Click to select PDF"

        # Draw the drop zone button
        self._draw_drop_zone()

        # Bind click events to entire canvas
        self.drop_zone.bind('<Button-1>', self._on_click_drop_zone)
        self.drop_zone.bind('<Enter>', self._on_drop_zone_enter)
        self.drop_zone.bind('<Leave>', self._on_drop_zone_leave)

        # Set up drag & drop if available
        if HAS_DND and isinstance(self.root, TkinterDnD.Tk):
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind('<<Drop>>', self._on_drop)
            self.drop_zone.dnd_bind('<<DragEnter>>', self._on_drag_enter)
            self.drop_zone.dnd_bind('<<DragLeave>>', self._on_drag_leave)

        # Page selection frame - improved layout
        page_frame = tk.Frame(main_frame, bg=NORD_COLORS['bg'])
        page_frame.grid(row=3, column=0, pady=(15, 0))

        # Page selection container with rounded background
        page_container = tk.Frame(
            page_frame,
            bg=NORD_COLORS['bg_lighter'],
            highlightthickness=1,
            highlightbackground=NORD_COLORS['bg_highlight']
        )
        page_container.pack(fill='x', padx=20)

        # Inner padding frame
        page_inner = tk.Frame(page_container, bg=NORD_COLORS['bg_lighter'])
        page_inner.pack(fill='x', padx=15, pady=12)

        # Page selection label - improved styling
        page_label_frame = tk.Frame(page_inner, bg=NORD_COLORS['bg_lighter'])
        page_label_frame.pack(anchor='w')

        page_label = tk.Label(
            page_label_frame,
            text="📄 Select Pages",
            font=("SF Pro", 12, "bold"),
            bg=NORD_COLORS['bg_lighter'],
            fg=NORD_COLORS['fg']
        )
        page_label.pack(side='left')

        # Optional badge
        optional_badge = tk.Label(
            page_label_frame,
            text="OPTIONAL",
            font=("SF Pro", 8, "bold"),
            bg=NORD_COLORS['bg_highlight'],
            fg=NORD_COLORS['fg_dim'],
            padx=6,
            pady=2
        )
        optional_badge.pack(side='left', padx=(8, 0))

        # Page entry field - improved with placeholder and border
        entry_frame = tk.Frame(page_inner, bg=NORD_COLORS['bg_lighter'])
        entry_frame.pack(fill='x', pady=(8, 0))

        self.page_entry = tk.Entry(
            entry_frame,
            font=("SF Pro", 13),
            bg=NORD_COLORS['bg'],
            fg=NORD_COLORS['fg'],
            insertbackground=NORD_COLORS['accent'],
            relief='flat',
            bd=0,
            highlightthickness=2,
            highlightcolor=NORD_COLORS['accent'],
            highlightbackground=NORD_COLORS['bg_highlight']
        )
        self.page_entry.pack(fill='x', ipady=8, ipadx=10)

        # Add placeholder text
        self.page_entry_placeholder = 'Leave empty for all pages, or enter: 1, 1-3, 1,3,5-7'
        self.page_entry.insert(0, self.page_entry_placeholder)
        self.page_entry.config(fg=NORD_COLORS['fg_dim'])

        # Bind events for placeholder behavior
        self.page_entry.bind('<FocusIn>', self._on_page_entry_focus_in)
        self.page_entry.bind('<FocusOut>', self._on_page_entry_focus_out)
        self.page_entry.bind('<KeyRelease>', self._on_page_entry_change)

        # Hint label - improved visibility
        hint_frame = tk.Frame(page_inner, bg=NORD_COLORS['bg_lighter'])
        hint_frame.pack(fill='x', pady=(6, 0))

        hint_icon = tk.Label(
            hint_frame,
            text="💡",
            font=("SF Pro", 10),
            bg=NORD_COLORS['bg_lighter']
        )
        hint_icon.pack(side='left')

        self.hint_label = tk.Label(
            hint_frame,
            text='Examples: "1" (first page), "1-3" (pages 1-3), "1,5,8-10" (mixed)',
            font=("SF Pro", 10),
            bg=NORD_COLORS['bg_lighter'],
            fg=NORD_COLORS['fg_dim'],
            justify='left'
        )
        self.hint_label.pack(side='left', padx=(5, 0))

        # Convert button
        self.convert_btn = ModernButton(
            main_frame,
            text="✨ Convert to Excel",
            command=self._convert,
            width=350,
            height=55,
            bg=NORD_COLORS['accent'],
            hover_bg=NORD_COLORS['frost']
        )
        self.convert_btn.grid(row=4, column=0, pady=(20, 25))
        self.convert_btn.set_state('disabled')

        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame,
            mode="indeterminate",
            length=500
        )
        self.progress.grid(row=5, column=0, pady=(0, 15))

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Ready. Please select a PDF file.",
            font=("SF Pro", 11),
            bg=NORD_COLORS['bg'],
            fg=NORD_COLORS['fg_dim']
        )
        self.status_label.grid(row=6, column=0)

    def _draw_drop_zone(self) -> None:
        """Draw the drop zone button - simple rectangle."""
        self.drop_zone.delete('all')

        width = 500
        height = 200

        # Simple rectangle with border
        self.drop_zone.create_rectangle(
            1, 1, width-1, height-1,
            fill=self.drop_zone_bg,
            outline=self.drop_zone_border,
            width=2
        )

        # Icon
        self.drop_zone.create_text(
            width/2, height/2 - 30,
            text=self.drop_zone_icon,
            font=("SF Pro", 50),
            fill=NORD_COLORS['fg']
        )

        # Text
        self.drop_zone.create_text(
            width/2, height/2 + 40,
            text=self.drop_zone_text,
            font=("SF Pro", 14),
            fill=NORD_COLORS['fg_dim']
        )

    def _on_click_drop_zone(self, event) -> None:
        """Handle click on drop zone."""
        # Don't allow browsing during conversion or if already browsing
        if self.is_converting or self.is_browsing:
            return
        self._browse_file()

    def _on_drop_zone_enter(self, event) -> None:
        """Handle mouse entering drop zone."""
        # Don't show hover effect if converting or browsing
        if self.is_converting or self.is_browsing:
            return

        if not self.pdf_path:
            # Highlight when hovering over empty drop zone
            self.drop_zone_bg = NORD_COLORS['bg_highlight']
            self.drop_zone_border = NORD_COLORS['accent']
        else:
            # Highlight selected zone
            self.drop_zone_border = NORD_COLORS['accent_yellow']

        self._draw_drop_zone()

    def _on_drop_zone_leave(self, event) -> None:
        """Handle mouse leaving drop zone."""
        # Don't change hover effect if converting or browsing
        if self.is_converting or self.is_browsing:
            return

        if not self.pdf_path:
            # Reset when leaving empty drop zone
            self.drop_zone_bg = NORD_COLORS['bg_lighter']
            self.drop_zone_border = NORD_COLORS['bg_highlight']
        else:
            # Reset to selected state
            self.drop_zone_border = NORD_COLORS['accent_green']

        self._draw_drop_zone()

    def _on_drag_enter(self, event) -> None:
        """Handle file dragged over drop zone."""
        # Don't show hover effect if converting or browsing
        if self.is_converting or self.is_browsing:
            return

        # Highlight drop zone
        self.drop_zone_bg = NORD_COLORS['bg_highlight']
        self.drop_zone_border = NORD_COLORS['accent']
        self._draw_drop_zone()

    def _on_drag_leave(self, event) -> None:
        """Handle file dragged away from drop zone."""
        # Reset to normal state
        if not self.pdf_path:
            self.drop_zone_bg = NORD_COLORS['bg_lighter']
            self.drop_zone_border = NORD_COLORS['bg_highlight']
        else:
            self.drop_zone_bg = NORD_COLORS['bg_highlight']
            self.drop_zone_border = NORD_COLORS['accent_green']
        self._draw_drop_zone()

    def _on_drop(self, event) -> None:
        """Handle file dropped on drop zone."""
        # Don't accept drops during conversion or browsing
        if self.is_converting or self.is_browsing:
            return

        # Parse the dropped file path
        # The data comes as a string, possibly with curly braces on Windows
        file_path = event.data

        # Clean up the path (remove curly braces if present)
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]

        # Handle multiple files (take first one)
        if ' ' in file_path and not Path(file_path).exists():
            # Multiple files might be space-separated
            # Try to find the first valid path
            parts = file_path.split(' ')
            for part in parts:
                clean_part = part.strip('{}')
                if clean_part and Path(clean_part).exists():
                    file_path = clean_part
                    break

        # Validate and set the file
        if file_path and Path(file_path).exists():
            self._set_pdf_file(file_path)
        else:
            self.status_label.config(
                text="Invalid file. Please drop a valid PDF file.",
                foreground=NORD_COLORS['accent_red']
            )

    def _browse_file(self) -> None:
        """Open file browser to select PDF."""
        # Prevent multiple dialogs from opening simultaneously
        if self.is_browsing:
            return

        # Set flag BEFORE try block
        self.is_browsing = True
        file_path = None

        try:
            file_path = filedialog.askopenfilename(
                parent=self.root,
                title="Select PDF File",
                filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
            )

        except Exception as e:
            self.status_label.config(
                text=f"Error: {str(e)}",
                foreground=NORD_COLORS['accent_red']
            )
        finally:
            # ALWAYS reset the flag first, before processing result
            self.is_browsing = False

        # Process the result after flag is reset
        if file_path:
            self._set_pdf_file(file_path)
        elif not self.pdf_path:
            # User cancelled and no file selected yet - restore status
            self.status_label.config(
                text="Ready. Please select a PDF file.",
                foreground=NORD_COLORS['fg_dim']
            )

    def _set_pdf_file(self, file_path: str) -> None:
        """Set the selected PDF file."""
        if not file_path.lower().endswith(".pdf"):
            messagebox.showerror("Error", "Please select a PDF file!")
            return

        self.pdf_path = file_path
        filename = Path(file_path).name

        # Get page count
        try:
            page_count = get_pdf_page_count(file_path)
            page_info = f" ({page_count} page{'s' if page_count > 1 else ''})"
        except Exception:
            page_info = ""

        # Update drop zone appearance
        self.drop_zone_bg = NORD_COLORS['bg_highlight']
        self.drop_zone_border = NORD_COLORS['accent_green']
        self.drop_zone_icon = "✅"
        self.drop_zone_text = f"{filename}"
        self._draw_drop_zone()

        # Update UI
        self.convert_btn.set_state('normal')
        self.status_label.config(
            text=f"Ready to convert: {filename}{page_info}",
            fg=NORD_COLORS['accent_green']
        )

    def _get_ocr_mode(self) -> int:
        """Get OCR mode (using default)."""
        return 3  # Default mode

    def _get_psm_mode(self) -> int:
        """Get PSM mode (using default)."""
        return 6  # Table mode

    def _on_page_entry_focus_in(self, event) -> None:
        """Handle focus in event for page entry (clear placeholder)."""
        if self.page_entry.get() == self.page_entry_placeholder:
            self.page_entry.delete(0, tk.END)
            self.page_entry.config(fg=NORD_COLORS['fg'])

    def _on_page_entry_focus_out(self, event) -> None:
        """Handle focus out event for page entry (restore placeholder if empty)."""
        if not self.page_entry.get().strip():
            self.page_entry.insert(0, self.page_entry_placeholder)
            self.page_entry.config(fg=NORD_COLORS['fg_dim'])

    def _on_page_entry_change(self, event) -> None:
        """Handle real-time validation of page entry - update bottom status."""
        # Don't validate placeholder text
        if self.page_entry.get() == self.page_entry_placeholder:
            return

        page_input = self.page_entry.get().strip()

        # Empty is valid (all pages) - restore original status
        if not page_input:
            if self.pdf_path:
                filename = Path(self.pdf_path).name
                try:
                    page_count = get_pdf_page_count(self.pdf_path)
                    page_info = f" ({page_count} page{'s' if page_count > 1 else ''})"
                except Exception:
                    page_info = ""
                self.status_label.config(
                    text=f"Ready to convert: {filename}{page_info}",
                    fg=NORD_COLORS['accent_green']
                )
            return

        # Try to parse and validate
        try:
            from .page_selector import parse_page_selection

            pages = parse_page_selection(page_input)

            # If we have a PDF selected, validate against page count
            if self.pdf_path and pages:
                try:
                    total_pages = get_pdf_page_count(self.pdf_path)
                    from .page_selector import validate_page_selection

                    valid_pages = validate_page_selection(pages, total_pages)
                    filename = Path(self.pdf_path).name

                    # Update status with success message
                    page_list = ', '.join(map(str, valid_pages))
                    self.status_label.config(
                        text=f"Ready to convert: {filename} - Pages: {page_list} ({len(valid_pages)} page{'s' if len(valid_pages) > 1 else ''})",
                        fg=NORD_COLORS['accent_green']
                    )
                except FileValidationError as e:
                    # Update status with error message
                    self.status_label.config(
                        text=f"⚠️ {str(e)}",
                        fg=NORD_COLORS['accent_red']
                    )
            else:
                # No PDF selected yet, just validate format
                if pages:
                    page_list = ', '.join(map(str, pages))
                    self.status_label.config(
                        text=f"Page selection valid: {page_list} ({len(pages)} page{'s' if len(pages) > 1 else ''})",
                        fg=NORD_COLORS['accent_blue']
                    )

        except FileValidationError as e:
            # Update status with error message
            self.status_label.config(
                text=f"⚠️ Invalid page format: {str(e)}",
                fg=NORD_COLORS['accent_red']
            )
        except Exception:
            # Generic error - show hint
            self.status_label.config(
                text='⚠️ Invalid page format. Use: "1", "1-3", or "1,3,5-7"',
                fg=NORD_COLORS['accent_yellow']
            )

    def _convert(self) -> None:
        """Start conversion process."""
        if not self.pdf_path:
            messagebox.showerror("Error", "Please select a PDF file first!")
            return

        # Ask for output location
        default_name = Path(self.pdf_path).stem + ".xlsx"
        output_path = filedialog.asksaveasfilename(
            title="Save Excel File As",
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
        )

        if not output_path:
            return  # User cancelled

        # Disable UI during conversion
        self._set_converting(True)

        # Start conversion in background thread
        thread = threading.Thread(
            target=self._do_conversion,
            args=(self.pdf_path, output_path),
            daemon=True,
        )
        thread.start()

    def _do_conversion(self, pdf_path: str, output_path: str) -> None:
        """Perform the actual conversion (runs in background thread)."""
        try:
            # Get page selection from entry field (ignore placeholder)
            page_input = self.page_entry.get().strip()
            if page_input == self.page_entry_placeholder:
                page_input = ""
            selected_pages = None

            if page_input:
                try:
                    total_pages = get_pdf_page_count(pdf_path)
                    selected_pages = parse_page_selection(page_input)
                    selected_pages = validate_page_selection(selected_pages, total_pages)

                    self.root.after(
                        0,
                        self._update_status,
                        f"🔍 Extracting pages {', '.join(map(str, selected_pages))}...",
                        NORD_COLORS['accent_blue']
                    )
                except FileValidationError as e:
                    self.root.after(0, self._show_error, "Invalid Page Selection", str(e))
                    return
            else:
                # Update status
                self.root.after(0, self._update_status, "🔍 Extracting and processing PDF...", NORD_COLORS['accent_blue'])

            # Extract with OCR
            ocr_mode = self._get_ocr_mode()
            psm_mode = self._get_psm_mode()

            extractor = OCRExtractor(
                languages=["tha", "eng"],
                ocr_mode=ocr_mode,
                psm_mode=psm_mode,
            )

            # Extract tables (includes OCR, parsing, and post-processing)
            tables = extractor.extract_tables_from_pdf(pdf_path, pages=selected_pages)

            if not tables or len(tables) == 0:
                self.root.after(
                    0,
                    self._show_error,
                    "No table found",
                    "Could not detect table structure in the PDF.\nThe PDF may not contain tabular data.",
                )
                return

            # Use first table
            table_data = tables[0]

            self.root.after(
                0, self._update_status, f"💾 Writing Excel file ({len(table_data)} rows)...", NORD_COLORS['accent_blue']
            )

            # Write to Excel
            writer = ExcelWriter()
            writer.write_table_to_excel(table_data, output_path, apply_formatting=True)

            # Success!
            self.root.after(0, self._show_success, output_path)

        except PDFToExcelError as e:
            self.root.after(0, self._show_error, "Conversion Error", str(e))
        except Exception as e:
            self.root.after(0, self._show_error, "Unexpected Error", str(e))
        finally:
            self.root.after(0, self._set_converting, False)

    def _set_converting(self, converting: bool) -> None:
        """Update UI for converting state."""
        self.is_converting = converting

        if converting:
            self.convert_btn.set_state('disabled')
            self.convert_btn.set_text("⏳ Converting...")
            self.page_entry.config(state='disabled')
            self.progress.start(10)
        else:
            self.convert_btn.set_state('normal')
            self.convert_btn.set_text("✨ Convert to Excel")
            self.page_entry.config(state='normal')
            self.progress.stop()

    def _update_status(self, message: str, color: str = NORD_COLORS['fg']) -> None:
        """Update status label."""
        self.status_label.config(text=message, foreground=color)

    def _show_success(self, output_path: str) -> None:
        """Show success message."""
        filename = Path(output_path).name
        self.status_label.config(
            text=f"✅ Success! Saved: {filename}",
            foreground=NORD_COLORS['accent_green']
        )

        messagebox.showinfo(
            "Success!",
            f"PDF converted successfully!\n\nOutput: {output_path}",
        )

    def _show_error(self, title: str, message: str) -> None:
        """Show error message."""
        self.status_label.config(
            text=f"❌ Error: {title}",
            foreground=NORD_COLORS['accent_red']
        )
        messagebox.showerror(title, message)


def main() -> None:
    """Run the GUI application."""
    # Use TkinterDnD if available for drag & drop support
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = PDFToExcelGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
