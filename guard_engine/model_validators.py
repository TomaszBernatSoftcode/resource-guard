from django.core.validators import RegexValidator


RESOURCE_PATTERN = RegexValidator(
    regex=r'^\d{3,}//\d{3,}//\d{3,}$',
    message='Invalid'
)
