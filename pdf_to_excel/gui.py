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
from .exceptions import PDFToExcelError


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
        self.root.geometry("650x550")
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
        self.convert_btn.grid(row=3, column=0, pady=(0, 25))
        self.convert_btn.set_state('disabled')

        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame,
            mode="indeterminate",
            length=500
        )
        self.progress.grid(row=4, column=0, pady=(0, 15))

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Ready. Please select a PDF file.",
            font=("SF Pro", 11),
            bg=NORD_COLORS['bg'],
            fg=NORD_COLORS['fg_dim']
        )
        self.status_label.grid(row=5, column=0)

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

        # Update drop zone appearance
        self.drop_zone_bg = NORD_COLORS['bg_highlight']
        self.drop_zone_border = NORD_COLORS['accent_green']
        self.drop_zone_icon = "✅"
        self.drop_zone_text = f"{filename}"
        self._draw_drop_zone()

        # Update UI
        self.convert_btn.set_state('normal')
        self.status_label.config(
            text=f"Ready to convert: {filename}",
            fg=NORD_COLORS['accent_green']
        )

    def _get_ocr_mode(self) -> int:
        """Get OCR mode (using default)."""
        return 3  # Default mode

    def _get_psm_mode(self) -> int:
        """Get PSM mode (using default)."""
        return 6  # Table mode

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
            tables = extractor.extract_tables_from_pdf(pdf_path)

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
            self.progress.start(10)
        else:
            self.convert_btn.set_state('normal')
            self.convert_btn.set_text("✨ Convert to Excel")
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
