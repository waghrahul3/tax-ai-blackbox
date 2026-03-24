"""
Unit tests for file_registry.py - role detection logic.
"""

from utils.file_registry import detect_file_info, FileRole


class TestFileRoleDetection:
    """Test file role detection for various filename patterns."""

    def test_federal_slip_summary_reference(self):
        """Test Federal Slip Summary files are classified as REFERENCE."""
        info = detect_file_info("Federal_Slips_Summary.pdf", "application/pdf", 1)
        
        assert info.role == FileRole.REFERENCE
        assert info.category == "Federal Slip Summary"
        assert info.role_label == "Federal Slip Summary (REFERENCE — compare against this)"
        assert info.index == 1

    def test_tax_software_summary_reference(self):
        """Test tax software summary files are classified as REFERENCE."""
        info = detect_file_info("taxprep_summary_2024.pdf", "application/pdf", 2)
        
        assert info.role == FileRole.REFERENCE
        assert info.category == "Tax Software Summary"

    def test_notice_of_assessment_reference(self):
        """Test NOA files are classified as REFERENCE."""
        info = detect_file_info("notice_of_assessment_2024.pdf", "application/pdf", 3)
        
        assert info.role == FileRole.REFERENCE
        assert info.category == "Notice of Assessment"

    def test_t4_slip_source(self):
        """Test T4 slip files are classified as SOURCE."""
        info = detect_file_info("Adam_s_T4_s.pdf", "application/pdf", 1)
        
        assert info.role == FileRole.SOURCE
        assert info.category == "T4 Slip"
        assert info.role_label == "T4 Slip (SOURCE — verify this document)"

    def test_t4e_slip_source(self):
        """Test T4E slip files are classified as SOURCE."""
        info = detect_file_info("Lizzie_T4E.jpg", "image/jpeg", 4)
        
        assert info.role == FileRole.SOURCE
        assert info.category == "T4E Slip"
        assert info.media_type == "image/jpeg"

    def test_t4a_slip_source(self):
        """Test T4A slip files are classified as SOURCE."""
        info = detect_file_info("contractor_T4A_2024.pdf", "application/pdf", 2)
        
        assert info.role == FileRole.SOURCE
        assert info.category == "T4A Slip"

    def test_t5_slip_source(self):
        """Test T5 slip files are classified as SOURCE."""
        info = detect_file_info("investment_T5.pdf", "application/pdf", 1)
        
        assert info.role == FileRole.SOURCE
        assert info.category == "T5 Slip"

    def test_t3_slip_source(self):
        """Test T3 slip files are classified as SOURCE."""
        info = detect_file_info("trust_T3.pdf", "application/pdf", 1)
        
        assert info.role == FileRole.SOURCE
        assert info.category == "T3 Slip"

    def test_t5008_slip_source(self):
        """Test T5008 slip files are classified as SOURCE."""
        info = detect_file_info("T5008_statements.pdf", "application/pdf", 1)
        
        assert info.role == FileRole.SOURCE
        assert info.category == "T5008 Slip"

    def test_rl1_slip_source(self):
        """Test RL-1 slip files are classified as SOURCE."""
        info = detect_file_info("RL1_2024.pdf", "application/pdf", 1)
        
        assert info.role == FileRole.SOURCE
        assert info.category == "RL-1 Slip"

    def test_rl3_slip_source(self):
        """Test RL-3 slip files are classified as SOURCE."""
        info = detect_file_info("RL3_statements.pdf", "application/pdf", 1)
        
        assert info.role == FileRole.SOURCE
        assert info.category == "RL-3 Slip"

    def test_bank_statement_source(self):
        """Test bank statements are classified as SOURCE."""
        info = detect_file_info("bank_statement_march.pdf", "application/pdf", 1)
        
        assert info.role == FileRole.SOURCE
        assert info.category == "Bank Statement"

    def test_invoice_source(self):
        """Test invoices are classified as SOURCE."""
        info = detect_file_info("invoice_12345.pdf", "application/pdf", 1)
        
        assert info.role == FileRole.SOURCE
        assert info.category == "Invoice / Receipt"

    def test_contract_supporting(self):
        """Test contracts are classified as SUPPORTING."""
        info = detect_file_info("employment_contract.pdf", "application/pdf", 1)
        
        assert info.role == FileRole.SUPPORTING
        assert info.category == "Contract"

    def test_letter_supporting(self):
        """Test letters are classified as SUPPORTING."""
        info = detect_file_info("correspondence_letter.pdf", "application/pdf", 1)
        
        assert info.role == FileRole.SUPPORTING
        assert info.category == "Correspondence"

    def test_unknown_file_fallback(self):
        """Test unknown files fall back to UNKNOWN with media type category."""
        info = detect_file_info("random_file.pdf", "application/pdf", 1)
        
        assert info.role == FileRole.UNKNOWN
        assert info.category == "PDF Document"
        assert info.role_label == "PDF Document (UNKNOWN — role unclear)"

    def test_unknown_image_fallback(self):
        """Test unknown images fall back to UNKNOWN with image category."""
        info = detect_file_info("scanned_doc.jpg", "image/jpeg", 1)
        
        assert info.role == FileRole.UNKNOWN
        assert info.category == "Scanned Image"

    def test_unknown_word_document_fallback(self):
        """Test unknown Word documents fall back to Word Document category."""
        info = detect_file_info("document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 1)
        
        assert info.role == FileRole.UNKNOWN
        assert info.category == "Word Document"

    def test_unknown_spreadsheet_fallback(self):
        """Test unknown spreadsheets fall back to Spreadsheet category."""
        info = detect_file_info("data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 1)
        
        assert info.role == FileRole.UNKNOWN
        assert info.category == "Spreadsheet"

    def test_unknown_generic_fallback(self):
        """Test completely unknown files fall back to Document category."""
        info = detect_file_info("file.txt", "text/plain", 1)
        
        assert info.role == FileRole.UNKNOWN
        assert info.category == "Document"

    def test_filename_normalization(self):
        """Test filename normalization (spaces, dashes, underscores)."""
        test_cases = [
            ("federal slip summary.pdf", FileRole.REFERENCE),
            ("federal-slip-summary.pdf", FileRole.REFERENCE),
            ("federal_slip_summary.pdf", FileRole.REFERENCE),
            ("FEDERAL_SLIP_SUMMARY.PDF", FileRole.REFERENCE),  # Case insensitive
            ("t4 slip.pdf", FileRole.SOURCE),
            ("t4-slip.pdf", FileRole.SOURCE),
            ("T4_SLIP.PDF", FileRole.SOURCE),
        ]
        
        for filename, expected_role in test_cases:
            info = detect_file_info(filename, "application/pdf", 1)
            assert info.role == expected_role, f"Failed for {filename}"

    def test_index_assignment(self):
        """Test index is properly assigned."""
        for i in range(1, 6):
            info = detect_file_info(f"file_{i}.pdf", "application/pdf", i)
            assert info.index == i

    def test_first_match_wins(self):
        """Test that rules are evaluated top-to-bottom, first match wins."""
        # This should match the first T4 rule, not fall through to anything else
        info = detect_file_info("T4_with_federal_slip_summary.pdf", "application/pdf", 1)
        assert info.role == FileRole.SOURCE  # T4 rule comes before federal slip rule
        assert info.category == "T4 Slip"
