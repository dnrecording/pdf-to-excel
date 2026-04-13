"""Unit tests for GUI application."""

import tkinter as tk
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from pdf_to_excel.gui import PDFToExcelGUI, ModernButton, NORD_COLORS


@pytest.fixture
def root():
    """Create a Tk root window for testing."""
    root = tk.Tk()
    yield root
    try:
        root.destroy()
    except:
        pass


@pytest.fixture
def gui_app(root):
    """Create a GUI application instance."""
    app = PDFToExcelGUI(root)
    return app


class TestModernButton:
    """Test the ModernButton custom widget."""

    def test_button_creation(self, root):
        """Test button can be created."""
        btn = ModernButton(
            root,
            text="Test Button",
            command=lambda: None,
            width=200,
            height=45
        )
        assert btn.text == "Test Button"
        assert btn.width == 200
        assert btn.height == 45

    def test_button_state_change(self, root):
        """Test button state can be changed."""
        btn = ModernButton(root, text="Test", command=lambda: None)

        # Initially not disabled
        assert not btn.is_disabled

        # Disable
        btn.set_state('disabled')
        assert btn.is_disabled

        # Enable
        btn.set_state('normal')
        assert not btn.is_disabled

    def test_button_text_change(self, root):
        """Test button text can be changed."""
        btn = ModernButton(root, text="Initial", command=lambda: None)
        assert btn.text == "Initial"

        btn.set_text("Updated")
        assert btn.text == "Updated"

    def test_button_click(self, root):
        """Test button click calls command."""
        mock_command = Mock()
        btn = ModernButton(root, text="Click Me", command=mock_command)

        # Simulate click
        event = Mock()
        btn._on_click(event)

        mock_command.assert_called_once()

    def test_button_disabled_no_click(self, root):
        """Test disabled button doesn't respond to clicks."""
        mock_command = Mock()
        btn = ModernButton(root, text="Test", command=mock_command)
        btn.set_state('disabled')

        # Simulate click
        event = Mock()
        btn._on_click(event)

        # Command should not be called
        mock_command.assert_not_called()


class TestPDFToExcelGUI:
    """Test the main GUI application."""

    def test_gui_initialization(self, gui_app):
        """Test GUI initializes correctly."""
        assert gui_app.pdf_path is None
        assert not gui_app.is_converting
        assert not gui_app.is_browsing
        assert gui_app.root.title() == "PDF to Excel Converter"

    def test_initial_state(self, gui_app):
        """Test initial UI state."""
        # Convert button should be disabled initially
        assert gui_app.convert_btn.is_disabled

        # No file selected
        assert gui_app.pdf_path is None

    @patch('pdf_to_excel.gui.filedialog.askopenfilename')
    def test_browse_file_success(self, mock_dialog, gui_app):
        """Test browsing and selecting a file."""
        mock_dialog.return_value = "/path/to/test.pdf"

        # Initially not browsing
        assert not gui_app.is_browsing

        gui_app._browse_file()

        # Should have set the PDF path
        assert gui_app.pdf_path == "/path/to/test.pdf"
        assert not gui_app.convert_btn.is_disabled

        # Flag should be reset after browsing
        assert not gui_app.is_browsing

    @patch('pdf_to_excel.gui.filedialog.askopenfilename')
    def test_browse_file_cancel(self, mock_dialog, gui_app):
        """Test cancelling file browse."""
        mock_dialog.return_value = ""  # User cancelled

        gui_app._browse_file()

        # Should not have set PDF path
        assert gui_app.pdf_path is None
        assert gui_app.convert_btn.is_disabled

        # Flag should be reset after cancelling
        assert not gui_app.is_browsing

    @patch('pdf_to_excel.gui.filedialog.askopenfilename')
    def test_browse_file_multiple_calls(self, mock_dialog, gui_app):
        """Test multiple browse calls work correctly."""
        # First call
        mock_dialog.return_value = "/path/to/first.pdf"
        gui_app._browse_file()
        assert gui_app.pdf_path == "/path/to/first.pdf"
        assert not gui_app.is_browsing

        # Second call should work
        mock_dialog.return_value = "/path/to/second.pdf"
        gui_app._browse_file()
        assert gui_app.pdf_path == "/path/to/second.pdf"
        assert not gui_app.is_browsing

        # Third call after cancel
        mock_dialog.return_value = ""
        gui_app._browse_file()
        assert gui_app.pdf_path == "/path/to/second.pdf"  # Should keep previous
        assert not gui_app.is_browsing

    @patch('pdf_to_excel.gui.filedialog.askopenfilename')
    def test_browse_prevents_concurrent_dialogs(self, mock_dialog, gui_app):
        """Test that multiple rapid clicks don't open multiple dialogs."""
        call_count = 0

        def slow_dialog(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Simulate that dialog takes time
            return "/path/to/test.pdf"

        mock_dialog.side_effect = slow_dialog

        # Set browsing flag manually to simulate first call in progress
        gui_app.is_browsing = True

        # Try to browse again - should be blocked
        gui_app._browse_file()

        # Dialog should not have been called
        assert call_count == 0

        # Reset flag
        gui_app.is_browsing = False

        # Now it should work
        gui_app._browse_file()
        assert call_count == 1

    def test_set_invalid_pdf_file(self, gui_app):
        """Test setting a non-PDF file shows error."""
        with patch('pdf_to_excel.gui.messagebox.showerror') as mock_error:
            gui_app._set_pdf_file("/path/to/file.txt")

            mock_error.assert_called_once()
            assert gui_app.pdf_path is None

    def test_set_valid_pdf_file(self, gui_app):
        """Test setting a valid PDF file."""
        gui_app._set_pdf_file("/path/to/test.pdf")

        assert gui_app.pdf_path == "/path/to/test.pdf"
        assert not gui_app.convert_btn.is_disabled

    def test_ocr_mode_default(self, gui_app):
        """Test OCR mode returns default value."""
        assert gui_app._get_ocr_mode() == 3

    def test_psm_mode_default(self, gui_app):
        """Test PSM mode returns default value."""
        assert gui_app._get_psm_mode() == 6

    def test_convert_without_file(self, gui_app):
        """Test convert button without selecting file."""
        with patch('pdf_to_excel.gui.messagebox.showerror') as mock_error:
            gui_app._convert()
            mock_error.assert_called_once()

    @patch('pdf_to_excel.gui.filedialog.asksaveasfilename')
    def test_convert_cancel_save_dialog(self, mock_save, gui_app):
        """Test cancelling the save dialog."""
        gui_app.pdf_path = "/path/to/input.pdf"
        mock_save.return_value = ""  # User cancelled

        gui_app._convert()

        # Should not start conversion
        assert not gui_app.is_converting

    @patch('pdf_to_excel.gui.threading.Thread')
    @patch('pdf_to_excel.gui.filedialog.asksaveasfilename')
    def test_convert_starts_thread(self, mock_save, mock_thread, gui_app):
        """Test convert starts background thread."""
        gui_app.pdf_path = "/path/to/input.pdf"
        mock_save.return_value = "/path/to/output.xlsx"

        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        gui_app._convert()

        # Should create and start thread
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

    def test_set_converting_state(self, gui_app):
        """Test UI state changes when converting."""
        gui_app.pdf_path = "/path/to/test.pdf"
        gui_app.convert_btn.set_state('normal')

        # Start converting
        gui_app._set_converting(True)
        assert gui_app.is_converting
        assert gui_app.convert_btn.is_disabled
        assert gui_app.convert_btn.text == "⏳ Converting..."

        # Stop converting
        gui_app._set_converting(False)
        assert not gui_app.is_converting
        assert not gui_app.convert_btn.is_disabled
        assert gui_app.convert_btn.text == "✨ Convert to Excel"

    def test_click_drop_zone_during_conversion(self, gui_app):
        """Test clicking drop zone during conversion is blocked."""
        gui_app.is_converting = True

        with patch.object(gui_app, '_browse_file') as mock_browse:
            event = Mock()
            gui_app._on_click_drop_zone(event)

            # Should not call browse
            mock_browse.assert_not_called()

    def test_hover_effects_during_browsing(self, gui_app):
        """Test hover effects are disabled during browsing."""
        gui_app.is_browsing = True
        original_border = gui_app.drop_zone_border

        event = Mock()
        gui_app._on_drop_zone_enter(event)

        # Border color should not change
        assert gui_app.drop_zone_border == original_border

    def test_status_label_updates(self, gui_app):
        """Test status label can be updated."""
        gui_app._update_status("Test message", NORD_COLORS['accent_green'])

        assert "Test message" in gui_app.status_label['text']
        assert gui_app.status_label['foreground'] == NORD_COLORS['accent_green']

    @patch('pdf_to_excel.gui.messagebox.showinfo')
    def test_show_success(self, mock_info, gui_app):
        """Test success message display."""
        gui_app._show_success("/path/to/output.xlsx")

        mock_info.assert_called_once()
        assert NORD_COLORS['accent_green'] == gui_app.status_label['foreground']

    @patch('pdf_to_excel.gui.messagebox.showerror')
    def test_show_error(self, mock_error, gui_app):
        """Test error message display."""
        gui_app._show_error("Test Error", "Error message")

        mock_error.assert_called_once()
        assert NORD_COLORS['accent_red'] == gui_app.status_label['foreground']

    @patch('pdf_to_excel.gui.filedialog.asksaveasfilename')
    @patch('pdf_to_excel.gui.filedialog.askopenfilename')
    def test_convert_button_click(self, mock_open, mock_save, gui_app):
        """Test clicking the convert button widget directly."""
        # Set up a file first
        mock_open.return_value = "/path/to/test.pdf"
        gui_app._browse_file()

        assert gui_app.pdf_path == "/path/to/test.pdf"
        assert not gui_app.convert_btn.is_disabled

        # Mock save dialog
        mock_save.return_value = "/path/to/output.xlsx"

        # Simulate clicking the button widget (not calling _convert directly)
        with patch('pdf_to_excel.gui.threading.Thread') as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance

            # Simulate click event on the button
            event = Mock()
            gui_app.convert_btn._on_click(event)

            # Should have called the convert method which starts a thread
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()

    def test_drag_enter(self, gui_app):
        """Test file dragged over drop zone shows hover effect."""
        # Save original state
        original_bg = gui_app.drop_zone_bg
        original_border = gui_app.drop_zone_border

        event = Mock()
        gui_app._on_drag_enter(event)

        # Should change appearance
        assert gui_app.drop_zone_bg == NORD_COLORS['bg_highlight']
        assert gui_app.drop_zone_border == NORD_COLORS['accent']

    def test_drag_enter_during_conversion(self, gui_app):
        """Test drag enter during conversion doesn't change appearance."""
        gui_app.is_converting = True
        original_bg = gui_app.drop_zone_bg

        event = Mock()
        gui_app._on_drag_enter(event)

        # Should not change
        assert gui_app.drop_zone_bg == original_bg

    def test_drag_leave(self, gui_app):
        """Test file dragged away from drop zone resets appearance."""
        # Start with highlight state
        gui_app.drop_zone_bg = NORD_COLORS['bg_highlight']
        gui_app.drop_zone_border = NORD_COLORS['accent']

        event = Mock()
        gui_app._on_drag_leave(event)

        # Should reset to normal
        assert gui_app.drop_zone_bg == NORD_COLORS['bg_lighter']
        assert gui_app.drop_zone_border == NORD_COLORS['bg_highlight']

    def test_drag_leave_with_file_selected(self, gui_app):
        """Test drag leave when file is already selected."""
        gui_app.pdf_path = "/path/to/test.pdf"

        event = Mock()
        gui_app._on_drag_leave(event)

        # Should reset to selected state
        assert gui_app.drop_zone_bg == NORD_COLORS['bg_highlight']
        assert gui_app.drop_zone_border == NORD_COLORS['accent_green']

    @patch('pdf_to_excel.gui.Path')
    @patch('pdf_to_excel.gui.messagebox.showerror')
    def test_drop_valid_pdf(self, mock_error, mock_path, gui_app):
        """Test dropping a valid PDF file."""
        # Mock Path to say file exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.name = "test.pdf"
        mock_path.return_value = mock_path_instance

        event = Mock()
        event.data = "/path/to/test.pdf"

        gui_app._on_drop(event)

        # Should set the file
        assert gui_app.pdf_path == "/path/to/test.pdf"
        assert not gui_app.convert_btn.is_disabled

    @patch('pdf_to_excel.gui.Path')
    def test_drop_file_with_curly_braces(self, mock_path, gui_app):
        """Test dropping file with curly braces (Windows format)."""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.name = "test.pdf"
        mock_path.return_value = mock_path_instance

        event = Mock()
        event.data = "{/path/to/test.pdf}"

        gui_app._on_drop(event)

        # Should strip curly braces and set file
        assert gui_app.pdf_path == "/path/to/test.pdf"

    @patch('pdf_to_excel.gui.Path')
    def test_drop_invalid_file(self, mock_path, gui_app):
        """Test dropping an invalid file."""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        event = Mock()
        event.data = "/path/to/nonexistent.pdf"

        gui_app._on_drop(event)

        # Should not set file
        assert gui_app.pdf_path is None
        assert NORD_COLORS['accent_red'] == gui_app.status_label['foreground']

    def test_drop_during_conversion(self, gui_app):
        """Test dropping file during conversion is blocked."""
        gui_app.is_converting = True

        event = Mock()
        event.data = "/path/to/test.pdf"

        original_path = gui_app.pdf_path
        gui_app._on_drop(event)

        # Should not change path
        assert gui_app.pdf_path == original_path

    def test_drop_during_browsing(self, gui_app):
        """Test dropping file during browsing is blocked."""
        gui_app.is_browsing = True

        event = Mock()
        event.data = "/path/to/test.pdf"

        original_path = gui_app.pdf_path
        gui_app._on_drop(event)

        # Should not change path
        assert gui_app.pdf_path == original_path
