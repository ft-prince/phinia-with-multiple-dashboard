from django import forms
from .models import ChecklistBase, SubgroupEntry, Verification, Concern

class ChecklistBaseForm(forms.ModelForm):
    class Meta:
        model = ChecklistBase
        exclude = ['shift', 'status', 'created_at']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'required': True
            })

            
            # Add specific validation attributes
            if field == 'line_pressure':
                self.fields[field].widget.attrs.update({
                    'min': '4.5',
                    'max': '5.5',
                    'step': '0.1',
                    'type': 'number'
                })
            elif field == 'uv_flow_input_pressure':
                self.fields[field].widget.attrs.update({
                    'min': '11',
                    'max': '15',
                    'step': '0.1',
                    'type': 'number'
                })
            elif field == 'test_pressure_vacuum':
                self.fields[field].widget.attrs.update({
                    'min': '0.25',
                    'max': '0.3',
                    'step': '0.01',
                    'type': 'number'
                })
            elif field in ['top_tool_id', 'bottom_tool_id', 'uv_assy_stage_id', 
                         'retainer_part_no', 'uv_clip_part_no', 'umbrella_part_no']:
                self.fields[field].widget.attrs.update({
                    'type': 'text',
                    'maxlength': '100'
                })
            elif field in ['oring_condition', 'master_verification_lvdt', 
                         'good_bad_master_verification', 'tool_alignment']:
                self.fields[field].widget = forms.Select(choices=[('OK', 'OK'), ('NG', 'NG')],
                                                       attrs={'class': 'form-control'})
            elif field == 'retainer_id_lubrication':
                self.fields[field].widget = forms.Select(choices=[('OK', 'OK'), ('NG', 'NG')],
                                                       attrs={'class': 'form-control'})
            elif field == 'error_proofing_verification':
                self.fields[field].widget = forms.Select(choices=[('Yes', 'Yes'), ('No', 'No')],
                                                       attrs={'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        errors = []

        # Validate required fields
        required_fields = [
            'selected_model', 'line_pressure', 'uv_flow_input_pressure', 
            'test_pressure_vacuum', 'oring_condition', 'master_verification_lvdt',
            'good_bad_master_verification', 'tool_alignment', 'top_tool_id',
            'bottom_tool_id', 'uv_assy_stage_id', 'retainer_part_no',
            'uv_clip_part_no', 'umbrella_part_no', 'retainer_id_lubrication',
            'error_proofing_verification'
        ]

        for field in required_fields:
            if not cleaned_data.get(field):
                errors.append(f"{field.replace('_', ' ').title()} is required.")

        # Validate numeric ranges
        try:
            line_pressure = float(cleaned_data.get('line_pressure', 0))
            if not (4.5 <= line_pressure <= 5.5):
                errors.append("Line pressure must be between 4.5 and 5.5 bar")
        except (TypeError, ValueError):
            errors.append("Invalid line pressure value")

        try:
            uv_pressure = float(cleaned_data.get('uv_flow_input_pressure', 0))
            if not (11 <= uv_pressure <= 15):
                errors.append("UV flow input pressure must be between 11 and 15 kPa")
        except (TypeError, ValueError):
            errors.append("Invalid UV flow input pressure value")

        try:
            test_pressure = float(cleaned_data.get('test_pressure_vacuum', 0))
            if not (0.25 <= test_pressure <= 0.3):
                errors.append("Test pressure vacuum must be between 0.25 and 0.3 MPa")
        except (TypeError, ValueError):
            errors.append("Invalid test pressure vacuum value")

        # Add validation errors if any found
        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data
    
class SubgroupEntryForm(forms.ModelForm):
    """Form for repeated measurements"""
    class Meta:
        model = SubgroupEntry
        exclude = ['checklist', 'subgroup_number', 'timestamp']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'required': True
            })

class VerificationForm(forms.ModelForm):
    """Form for verifications"""
    class Meta:
        model = Verification
        fields = ['comments']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comments'].widget.attrs.update({'class': 'form-control'})

class ConcernForm(forms.ModelForm):
    """Form for concerns and actions"""
    class Meta:
        model = Concern
        exclude = ['checklist', 'manufacturing_approval', 'quality_approval', 'created_at']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            
            
            

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    user_type = forms.ChoiceField(choices=User.USER_TYPES)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'user_type', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})            