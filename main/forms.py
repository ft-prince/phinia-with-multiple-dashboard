from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, ChecklistBase, SubgroupEntry, Verification, Concern, SubgroupVerification

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

            # Update field attributes without validation restrictions
            if field == 'line_pressure':
                self.fields[field].widget.attrs.update({
                    'type': 'number',
                    'step': 'any',  # Allows any decimal value
                    'placeholder': 'Recommended: 4.5 - 5.5 bar'
                })
            elif field == 'uv_flow_input_pressure':
                self.fields[field].widget.attrs.update({
                    'type': 'number',
                    'step': 'any',
                    'placeholder': 'Recommended: 11 - 15 kPa'
                })
            elif field == 'test_pressure_vacuum':
                self.fields[field].widget.attrs.update({
                    'type': 'number',
                    'step': 'any',
                    'placeholder': 'Recommended: 0.25 - 0.3 MPa'
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
        warnings = []

        # Check required fields
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
                raise forms.ValidationError(f"{field.replace('_', ' ').title()} is required.")

        # Add warnings for values outside recommended ranges (but don't raise validation errors)
        try:
            line_pressure = float(cleaned_data.get('line_pressure', 0))
            if not (4.5 <= line_pressure <= 5.5):
                warnings.append(f"Line pressure {line_pressure} is outside recommended range (4.5 - 5.5 bar)")
        except (TypeError, ValueError):
            pass

        try:
            uv_pressure = float(cleaned_data.get('uv_flow_input_pressure', 0))
            if not (11 <= uv_pressure <= 15):
                warnings.append(f"UV flow input pressure {uv_pressure} is outside recommended range (11 - 15 kPa)")
        except (TypeError, ValueError):
            pass

        try:
            test_pressure = float(cleaned_data.get('test_pressure_vacuum', 0))
            if not (0.25 <= test_pressure <= 0.3):
                warnings.append(f"Test pressure vacuum {test_pressure} is outside recommended range (0.25 - 0.3 MPa)")
        except (TypeError, ValueError):
            pass

        # Store warnings in the form for display (but don't prevent submission)
        if warnings:
            self.warnings = warnings

        return cleaned_data

class SubgroupEntryForm(forms.ModelForm):
    """Form for repeated measurements"""
    class Meta:
        model = SubgroupEntry
        exclude = ['checklist', 'subgroup_number', 'timestamp', 'verification_status']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'required': True
            })
            
            # Update measurement fields to allow any value
            if field == 'uv_vacuum_test':
                self.fields[field].widget.attrs.update({
                    'type': 'number',
                    'step': 'any',
                    'placeholder': 'Recommended: -43 to -35 kPa'
                })
            elif field == 'uv_flow_value':
                self.fields[field].widget.attrs.update({
                    'type': 'number',
                    'step': 'any',
                    'placeholder': 'Recommended: 30-40 LPM'
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

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    user_type = forms.ChoiceField(choices=User.USER_TYPES)
    company_id = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'company_id', 'user_type', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})

class SubgroupVerificationForm(forms.ModelForm):
    """Form for subgroup verifications"""
    class Meta:
        model = SubgroupVerification
        fields = ['status', 'comments']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].widget.attrs.update({'class': 'form-control'})
        self.fields['comments'].widget.attrs.update({
            'class': 'form-control',
            'rows': '3'
        })