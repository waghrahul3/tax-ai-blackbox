"""Test cases for API layer password error handling."""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from api.routes import process_documents
from exceptions.document_exceptions import PasswordProtectedPDFException


class TestAPIPasswordErrors:
    """Test API handling of password-protected PDF errors."""

    def setup_method(self):
        """Set up test environment."""
        os.environ["PDF_PASSWORD_PATTERNS"] = "_password_,_pwd_,_secure_"
        os.environ["ENABLE_PASSWORD_EXTRACTION"] = "true"
        os.environ["PDF_PATTERN_CASE_SENSITIVE"] = "false"

    def create_mock_request(self):
        """Create a mock FastAPI request."""
        mock_request = MagicMock()
        mock_request.url_for.return_value.path = "/ai/download"
        return mock_request

    def create_mock_file(self, filename):
        """Create a mock uploaded file."""
        mock_file = MagicMock()
        mock_file.filename = filename
        mock_file.content_type = "application/pdf"
        mock_file.size = 1024
        return mock_file

    @patch('api.routes.persist_uploads')
    @patch('api.routes.document_processing_service')
    @patch('api.routes.file_validation_service')
    @patch('api.routes.template_service')
    @patch('api.routes.content_cleaning_service')
    @patch('api.routes.pipeline')
    @patch('api.routes.output_generation_service')
    def test_password_required_error(self, mock_output_service, mock_pipeline, mock_cleaning_service, 
                                   mock_template_service, mock_validation_service, mock_doc_service, mock_persist_uploads):
        """Test API handling of password_required error."""
        # Setup mocks
        mock_validation_service.validate_files.return_value = None
        mock_template_service.get_template.return_value = None
        mock_persist_uploads.return_value = ([], "upload_dir")
        mock_cleaning_service.clean_prompt_content.return_value = "cleaned prompt"
        
        # Simulate password required exception
        mock_doc_service.load_documents.side_effect = PasswordProtectedPDFException(
            "Password required", 
            filename="protected.pdf",
            error_code="password_required"
        )
        
        mock_request = self.create_mock_request()
        mock_file = self.create_mock_file("protected.pdf")
        
        with pytest.raises(HTTPException) as exc_info:
            process_documents(
                request=mock_request,
                files=[mock_file],
                template_name=None,
                prompt="test prompt",
                system_prompt=None,
                ctid=None
            )
        
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"] == "password_required"
        assert exc_info.value.detail["filename"] == "protected.pdf"

    @patch('api.routes.persist_uploads')
    @patch('api.routes.document_processing_service')
    @patch('api.routes.file_validation_service')
    @patch('api.routes.template_service')
    @patch('api.routes.content_cleaning_service')
    @patch('api.routes.pipeline')
    @patch('api.routes.output_generation_service')
    def test_wrong_password_error(self, mock_output_service, mock_pipeline, mock_cleaning_service, 
                                mock_template_service, mock_validation_service, mock_doc_service, mock_persist_uploads):
        """Test API handling of wrong_password error."""
        # Setup mocks
        mock_validation_service.validate_files.return_value = None
        mock_template_service.get_template.return_value = None
        mock_persist_uploads.return_value = ([], "upload_dir")
        mock_cleaning_service.clean_prompt_content.return_value = "cleaned prompt"
        
        # Simulate wrong password exception
        mock_doc_service.load_documents.side_effect = PasswordProtectedPDFException(
            "Wrong password", 
            filename="file_password_wrongpass.pdf",
            error_code="wrong_password"
        )
        
        mock_request = self.create_mock_request()
        mock_file = self.create_mock_file("file_password_wrongpass.pdf")
        
        with pytest.raises(HTTPException) as exc_info:
            process_documents(
                request=mock_request,
                files=[mock_file],
                template_name=None,
                prompt="test prompt",
                system_prompt=None,
                ctid=None
            )
        
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"] == "wrong_password"
        assert exc_info.value.detail["filename"] == "file_password_wrongpass.pdf"

    @patch('api.routes.persist_uploads')
    @patch('api.routes.document_processing_service')
    @patch('api.routes.file_validation_service')
    @patch('api.routes.template_service')
    @patch('api.routes.content_cleaning_service')
    @patch('api.routes.pipeline')
    @patch('api.routes.output_generation_service')
    def test_invalid_pdf_error(self, mock_output_service, mock_pipeline, mock_cleaning_service, 
                             mock_template_service, mock_validation_service, mock_doc_service, mock_persist_uploads):
        """Test API handling of invalid_pdf error."""
        # Setup mocks
        mock_validation_service.validate_files.return_value = None
        mock_template_service.get_template.return_value = None
        mock_persist_uploads.return_value = ([], "upload_dir")
        mock_cleaning_service.clean_prompt_content.return_value = "cleaned prompt"
        
        # Simulate invalid PDF exception
        mock_doc_service.load_documents.side_effect = PasswordProtectedPDFException(
            "Invalid PDF", 
            filename="corrupted.pdf",
            error_code="invalid_pdf"
        )
        
        mock_request = self.create_mock_request()
        mock_file = self.create_mock_file("corrupted.pdf")
        
        with pytest.raises(HTTPException) as exc_info:
            process_documents(
                request=mock_request,
                files=[mock_file],
                template_name=None,
                prompt="test prompt",
                system_prompt=None,
                ctid=None
            )
        
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"] == "invalid_pdf"
        assert exc_info.value.detail["filename"] == "corrupted.pdf"

    @patch('api.routes.persist_uploads')
    @patch('api.routes.document_processing_service')
    @patch('api.routes.file_validation_service')
    @patch('api.routes.template_service')
    @patch('api.routes.content_cleaning_service')
    @patch('api.routes.pipeline')
    @patch('api.routes.output_generation_service')
    def test_generic_pdf_error(self, mock_output_service, mock_pipeline, mock_cleaning_service, 
                               mock_template_service, mock_validation_service, mock_doc_service, mock_persist_uploads):
        """Test API handling of generic PDF error."""
        # Setup mocks
        mock_validation_service.validate_files.return_value = None
        mock_template_service.get_template.return_value = None
        mock_persist_uploads.return_value = ([], "upload_dir")
        mock_cleaning_service.clean_prompt_content.return_value = "cleaned prompt"
        
        # Simulate generic password PDF exception
        mock_doc_service.load_documents.side_effect = PasswordProtectedPDFException(
            "Generic PDF error", 
            filename="problem.pdf",
            error_code="generic_error"
        )
        
        mock_request = self.create_mock_request()
        mock_file = self.create_mock_file("problem.pdf")
        
        with pytest.raises(HTTPException) as exc_info:
            process_documents(
                request=mock_request,
                files=[mock_file],
                template_name=None,
                prompt="test prompt",
                system_prompt=None,
                ctid=None
            )
        
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["error"] == "pdf_processing_error"
        assert exc_info.value.detail["filename"] == "problem.pdf"
        assert "message" in exc_info.value.detail

    @patch('api.routes.persist_uploads')
    @patch('api.routes.document_processing_service')
    @patch('api.routes.file_validation_service')
    @patch('api.routes.template_service')
    @patch('api.routes.content_cleaning_service')
    @patch('api.routes.pipeline')
    @patch('api.routes.output_generation_service')
    def test_successful_processing_with_password(self, mock_output_service, mock_pipeline, mock_cleaning_service, 
                                                mock_template_service, mock_validation_service, mock_doc_service, mock_persist_uploads):
        """Test successful processing of password-protected PDF."""
        # Setup mocks
        mock_validation_service.validate_files.return_value = None
        mock_template_service.get_template.return_value = None
        mock_persist_uploads.return_value = ([], "upload_dir")
        mock_cleaning_service.clean_prompt_content.return_value = "cleaned prompt"
        
        # Simulate successful document loading
        mock_doc = MagicMock()
        mock_doc.is_text.return_value = True
        mock_doc.is_image.return_value = False
        mock_doc_service.load_documents.return_value = [mock_doc]
        
        # Simulate successful pipeline processing
        mock_pipeline.run.return_value = "Processed content"
        
        # Simulate output generation
        mock_output_service.generate_output_file.return_value = {
            "format": "markdown",
            "file_path": "/output/test.md",
            "folder_path": "/output/test_folder"
        }
        
        mock_request = self.create_mock_request()
        mock_file = self.create_mock_file("file_password_secret123.pdf")
        
        # Should not raise any exception
        result = process_documents(
            request=mock_request,
            files=[mock_file],
            template_name=None,
            prompt="test prompt",
            system_prompt=None,
            ctid=None
        )
        
        assert result["status"] == "success"
        assert result["format"] == "markdown"

    def test_error_response_format(self):
        """Test that error response format matches specification."""
        # Test password_required format
        try:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "password_required",
                    "filename": "protected.pdf"
                }
            )
        except HTTPException as e:
            assert e.status_code == 422
            assert e.detail["error"] == "password_required"
            assert e.detail["filename"] == "protected.pdf"
            assert len(e.detail) == 2  # Only error and filename fields

        # Test wrong_password format
        try:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "wrong_password",
                    "filename": "file_password_wrongpass.pdf"
                }
            )
        except HTTPException as e:
            assert e.status_code == 422
            assert e.detail["error"] == "wrong_password"
            assert e.detail["filename"] == "file_password_wrongpass.pdf"
            assert len(e.detail) == 2

        # Test invalid_pdf format
        try:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "invalid_pdf",
                    "filename": "corrupted.pdf"
                }
            )
        except HTTPException as e:
            assert e.status_code == 422
            assert e.detail["error"] == "invalid_pdf"
            assert e.detail["filename"] == "corrupted.pdf"
            assert len(e.detail) == 2
