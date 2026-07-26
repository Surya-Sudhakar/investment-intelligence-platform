from typing import cast

from fastapi import Request

from app.modules.assessments.service import AssessmentService


def get_assessment_service(request: Request) -> AssessmentService:
    return cast(AssessmentService, request.app.state.assessment_service)
