from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError, FieldError, ObjectDoesNotExist
from django.db import IntegrityError
from .responses import error_response
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """Global exception handler with unified response format."""
    
    # Handle IntegrityError (database constraint violations)
    if isinstance(exc, IntegrityError):
        error_message = str(exc)
        
        # Extract field name from error message
        if "null value in column" in error_message:
            # Parse: null value in column "entry_year" of relation "cohorts"
            column = error_message.split('"')[1] if '"' in error_message else "unknown"
            return error_response(
                message=f"Required field '{column}' is missing",
                errors={column: ["This field is required"]},
                error_code="INTEGRITY_ERROR",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        elif "duplicate key" in error_message:
            return error_response(
                message="Duplicate entry: This record already exists",
                error_code="DUPLICATE_ENTRY",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Generic integrity error fallback
        logger.warning(f"Unhandled IntegrityError: {error_message}")
        return error_response(
            message="Database constraint violation",
            error_code="INTEGRITY_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle FieldError (invalid query params like ordering)
    if isinstance(exc, FieldError):
        return error_response(
            message=f"Invalid query parameter: {str(exc)}",
            error_code="INVALID_FIELD_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle RelatedObjectDoesNotExist
    if isinstance(exc, ObjectDoesNotExist):
        model_name = exc.__class__.__name__
        error_message = str(exc)
        
        if "has no" in error_message:
            return error_response(
                message=f"Required related object missing: {error_message}",
                error_code="RELATED_OBJECT_NOT_FOUND",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return error_response(
            message=f"{model_name} not found",
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Handle Django ValidationError
    if isinstance(exc, DjangoValidationError):
        errors = exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages}
        return error_response(
            message="Validation Error",
            errors=errors,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    response = exception_handler(exc, context)
    
    if response is not None:
        if isinstance(exc, DRFValidationError):
            errors = response.data
            view = context.get('view')
            
            if view and hasattr(view, 'get_serializer_class'):
                try:
                    serializer_class = view.get_serializer_class()
                    model = serializer_class.Meta.model
                    
                    for field_name, error_list in errors.items():
                        try:
                            model_field = model._meta.get_field(field_name)
                            if hasattr(model_field, 'choices') and model_field.choices:
                                valid_choices = dict(model_field.choices)
                                choices_str = ", ".join(valid_choices.keys())
                                errors[field_name] = [
                                    f"{error}. Valid choices: {choices_str}"
                                    for error in error_list
                                ]
                        except (FieldError, AttributeError):
                            pass
                except Exception as e:
                    logger.debug(f"Could not enrich validation errors: {e}")
            
            return error_response(
                message="Validation Error",
                errors=errors,
                error_code="VALIDATION_ERROR",
                status_code=response.status_code
            )

        error_message = str(exc.detail) if hasattr(exc, 'detail') else str(exc)
        return error_response(
            message=error_message,
            error_code=exc.__class__.__name__.upper(),
            status_code=response.status_code
        )
    
    logger.exception(f"Unhandled exception in {context['view']}: {exc}")
    return error_response(
        message="Internal Server Error",
        error_code="INTERNAL_SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )