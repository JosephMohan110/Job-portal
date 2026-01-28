# admin_self/ml_utils.py
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
import os
from django.conf import settings

class XGBoostPredictor:
    """Handle XGBoost model loading and predictions"""
    
    def __init__(self):
        self.models = None
        self.features = None
        self.metadata = None
        self.loaded = False
        self.model_path = os.path.join(settings.BASE_DIR, 'xg_boost', 'jobportal_xgboost_models_complete.pkl')
        
    def load_model(self):
        """Load the XGBoost model from file"""
        try:
            if not os.path.exists(self.model_path):
                print(f"Model file not found at: {self.model_path}")
                return False
            
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
            
            self.models = data.get('models', {})
            self.features = data.get('feature_names', [])
            self.metadata = data.get('metadata', {})
            self.loaded = True
            
            print(f"Loaded {len(self.models)} models successfully")
            print(f"Available features: {self.features[:10]}...")  # Print first 10 features
            return True
            
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            return False
    
    def get_available_predictions(self):
        """Get list of available prediction targets"""
        if not self.loaded:
            self.load_model()
        
        return list(self.models.keys()) if self.models else []
    
    def prepare_features(self, platform_data):
        """
        Prepare features for prediction based on current platform data
        
        Args:
            platform_data: dict containing current platform metrics
        """
        # Get current date information
        now = datetime.now()
        
        # Base feature template based on error message
        features = {
            # Core platform metrics
            'total_employers': platform_data.get('total_employers', 0),
            'total_employees': platform_data.get('total_workers', 0),
            'platform_commission': float(platform_data.get('platform_commission', 0)),
            'total_commission': float(platform_data.get('platform_commission', 0)),
            
            # Time-based features
            'date_year': now.year,
            'date_month': now.month,
            'date_day': now.day,
            'registration_date_year': now.year,
            'registration_date_month': now.month,
            'registration_date_day': now.day,
            'last_active_date_year': now.year,
            'last_active_date_month': now.month,
            'last_active_date_day': now.day,
            
            # User status
            'account_status': 1,  # Active
            'deletion_date': 0,  # Not deleted
            'deletions': platform_data.get('deleted_accounts_this_month', 0),
            
            # Location features (default values)
            'district': 'unknown',
            'payment_disputes': 0,
            
            # Derived features from error message
            'contracts_signed': platform_data.get('completed_bookings', 0),
            'engagement_score': min(100, platform_data.get('active_users', 0) / max(platform_data.get('total_users', 1), 1) * 100),
            'total_users': platform_data.get('total_users', 0),
            'user_type': 0.5,  # Mixed
            'earning_per_job': float(platform_data.get('avg_earning_per_job', 0)),
            'active_users': platform_data.get('active_users', 0),
            'days_since_registration': 180,  # Average days
            'completion_rate': platform_data.get('success_rate', 0) / 100 if platform_data.get('success_rate', 0) > 0 else 0,
            'favorite_employee_count': platform_data.get('total_users', 0) * 0.3,  # Estimate
            'new_signups': platform_data.get('new_users_this_month', 0),
            'cancelled_within_3_days': platform_data.get('cancelled_bookings', 0) * 0.1,  # Estimate
            'times_favorited': platform_data.get('total_bookings', 0) * 0.2,  # Estimate
            'certificates_uploaded': platform_data.get('total_users', 0) * 0.1,  # Estimate
            'support_tickets': platform_data.get('total_users', 0) * 0.05,  # Estimate
            'job_category': 3,  # Mixed category
            
            # Additional features that might be expected
            'platform_active_users': platform_data.get('active_users', 0),
            'platform_new_signups': platform_data.get('new_users_this_month', 0),
            'platform_deletions': platform_data.get('deleted_accounts_this_month', 0),
            'total_bookings': platform_data.get('total_bookings', 0),
            'completed_bookings': platform_data.get('completed_bookings', 0),
            'cancelled_bookings': platform_data.get('cancelled_bookings', 0),
            'success_rate': platform_data.get('success_rate', 0),
            'avg_rating': platform_data.get('avg_rating', 0),
            'total_reviews': platform_data.get('total_reviews', 0),
            'total_spent': float(platform_data.get('total_revenue', 0)),
            'total_earned': float(platform_data.get('total_earnings', 0)),
            'total_amount_in_site': float(platform_data.get('total_revenue', 0)),
            'avg_earning_per_job': float(platform_data.get('avg_earning_per_job', 0)),
            'avg_spending_per_job': float(platform_data.get('avg_spending_per_job', 0)),
        }
        
        # Convert to DataFrame
        features_df = pd.DataFrame([features])
        
        # Ensure we have all expected features from the model
        if self.features:
            # Add missing features with default values
            for feature in self.features:
                if feature not in features_df.columns:
                    features_df[feature] = 0
        
        return features_df
    
    def predict(self, platform_data):
        """Make predictions for all targets"""
        if not self.loaded:
            if not self.load_model():
                return {}
        
        try:
            # Prepare features
            features_df = self.prepare_features(platform_data)
            
            # Make predictions for all models
            predictions = {}
            
            for target, model in self.models.items():
                try:
                    # Ensure features are in correct order
                    if hasattr(model, 'feature_names_in_'):
                        # Reorder columns to match model's expected order
                        expected_features = model.feature_names_in_
                        features_df_aligned = features_df.reindex(columns=expected_features, fill_value=0)
                        prediction = model.predict(features_df_aligned)[0]
                    else:
                        prediction = model.predict(features_df)[0]
                    
                    # Handle classification vs regression
                    if hasattr(model, 'predict_proba'):
                        # Classification model
                        proba = model.predict_proba(features_df)[0]
                        if len(proba) > 1:
                            prediction = proba[1]  # Probability of positive class
                    
                    # Ensure prediction is reasonable based on target type
                    if 'rate' in target.lower() or 'success' in target.lower():
                        prediction = max(0, min(100, prediction))
                    elif 'rating' in target.lower():
                        prediction = max(0, min(5, prediction))
                    elif any(word in target.lower() for word in ['bookings', 'users', 'count', 'reviews']):
                        prediction = max(0, prediction)
                    
                    predictions[target] = float(prediction)
                    
                except Exception as e:
                    print(f"Error predicting {target}: {str(e)}")
                    predictions[target] = 0.0
            
            return predictions
            
        except Exception as e:
            print(f"Error in prediction: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_feature_importance(self):
        """Get feature importance from models"""
        if not self.loaded:
            self.load_model()
        
        if not self.models:
            return {}
        
        # Calculate average importance across all models
        feature_importance = {}
        
        for target, model in self.models.items():
            try:
                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                    
                    # Get feature names
                    if hasattr(model, 'feature_names_in_'):
                        feature_names = model.feature_names_in_
                    elif self.features:
                        feature_names = self.features
                    else:
                        continue
                    
                    if len(feature_names) == len(importances):
                        for i, importance in enumerate(importances):
                            feature_name = feature_names[i] if i < len(feature_names) else f"feature_{i}"
                            feature_importance[feature_name] = feature_importance.get(feature_name, 0) + importance
            except:
                continue
        
        # Normalize importance scores
        if feature_importance:
            total = sum(feature_importance.values())
            if total > 0:
                feature_importance = {k: v/total for k, v in feature_importance.items()}
        
        return dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10])


# Singleton instance
predictor = XGBoostPredictor()