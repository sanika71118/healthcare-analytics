import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

class HealthcareDataGenerator:
    """Generate synthetic healthcare patient data"""
    
    def __init__(self, n_patients=7000):
        self.n_patients = n_patients
        
    def generate_patients(self):
        """Generate patient demographic data"""
        
        # Patient IDs
        patient_ids = [f"PT{str(i).zfill(6)}" for i in range(1, self.n_patients + 1)]
        
        # Demographics
        ages = np.random.normal(45, 18, self.n_patients).clip(18, 95).astype(int)
        genders = np.random.choice(['Male', 'Female'], self.n_patients, p=[0.48, 0.52])
        
        # Medical conditions (correlated with age)
        conditions = []
        for age in ages:
            if age < 30:
                cond = np.random.choice(['None', 'Asthma', 'Allergies'], p=[0.7, 0.2, 0.1])
            elif age < 50:
                cond = np.random.choice(['None', 'Hypertension', 'Diabetes', 'Asthma'], 
                                       p=[0.5, 0.25, 0.15, 0.1])
            else:
                cond = np.random.choice(['Hypertension', 'Diabetes', 'Heart Disease', 'Arthritis'], 
                                       p=[0.4, 0.3, 0.2, 0.1])
            conditions.append(cond)
        
        # Insurance types
        insurance = np.random.choice(['Private', 'Medicare', 'Medicaid', 'Uninsured'], 
                                    self.n_patients, p=[0.5, 0.25, 0.15, 0.1])
        
        # Hospital visits (Poisson distribution)
        visits_per_year = np.random.poisson(2, self.n_patients)
        
        # Treatment costs (log-normal distribution)
        avg_costs = np.random.lognormal(8, 1, self.n_patients)
        
        # Satisfaction scores (1-10)
        satisfaction = np.random.normal(7.5, 1.5, self.n_patients).clip(1, 10).round(1)
        
        # Previous admissions
        prev_admissions = np.random.poisson(1, self.n_patients)
        
        # Comorbidity count (additional conditions)
        comorbidity = np.zeros(self.n_patients)
        for i, age in enumerate(ages):
            if age > 60:
                comorbidity[i] = np.random.poisson(1.5)
            elif age > 40:
                comorbidity[i] = np.random.poisson(0.8)
            else:
                comorbidity[i] = np.random.poisson(0.3)
        
        # Emergency visits ratio
        emergency_ratio = np.random.beta(2, 5, self.n_patients)
        
        # Length of stay (average)
        avg_los = np.random.gamma(2, 2, self.n_patients)
        
        # Lab abnormalities (percentage)
        lab_abnormal = np.random.beta(3, 7, self.n_patients)
        
        # Readmission flag (correlated with multiple factors)
        readmission_prob = (
            (ages / 200) + 
            (conditions != 'None') * 0.15 +
            (prev_admissions / 10) +
            (comorbidity / 10) +
            (emergency_ratio * 0.3) +
            (lab_abnormal * 0.2) +
            np.random.normal(0, 0.05, self.n_patients)
        ).clip(0, 0.9)
        
        readmissions = np.random.binomial(1, readmission_prob)
        
        return pd.DataFrame({
            'patient_id': patient_ids,
            'age': ages,
            'gender': genders,
            'condition': conditions,
            'insurance_type': insurance,
            'visits_per_year': visits_per_year,
            'avg_treatment_cost': avg_costs.round(2),
            'satisfaction_score': satisfaction,
            'prev_admissions': prev_admissions,
            'comorbidity_count': comorbidity.astype(int),
            'emergency_ratio': emergency_ratio.round(3),
            'avg_length_of_stay': avg_los.round(1),
            'lab_abnormality_rate': lab_abnormal.round(3),
            'readmitted': readmissions.astype(bool)
        })
    
    def generate_visits(self, patients_df):
        """Generate individual visit records"""
        
        visits = []
        visit_id = 1
        
        for _, patient in patients_df.iterrows():
            n_visits = patient['visits_per_year']
            
            for _ in range(n_visits):
                # Random visit date in past year
                days_ago = np.random.randint(0, 365)
                visit_date = datetime.now() - timedelta(days=days_ago)
                
                # Visit type
                visit_type = np.random.choice(['Emergency', 'Outpatient', 'Inpatient'], 
                                             p=[0.2, 0.5, 0.3])
                
                # Duration (days for inpatient, hours for others)
                if visit_type == 'Inpatient':
                    duration = np.random.poisson(3) + 1
                else:
                    duration = np.random.uniform(0.5, 4).round(1)
                
                # Cost varies by visit type
                if visit_type == 'Emergency':
                    cost = np.random.uniform(1000, 5000)
                elif visit_type == 'Inpatient':
                    cost = np.random.uniform(5000, 25000)
                else:
                    cost = np.random.uniform(200, 2000)
                
                visits.append({
                    'visit_id': f"V{str(visit_id).zfill(8)}",
                    'patient_id': patient['patient_id'],
                    'visit_date': visit_date.strftime('%Y-%m-%d'),
                    'visit_type': visit_type,
                    'duration': duration,
                    'cost': round(cost, 2),
                    'department': np.random.choice(['Cardiology', 'Neurology', 'Orthopedics', 
                                                   'General Medicine', 'Emergency'])
                })
                visit_id += 1
        
        return pd.DataFrame(visits)


class ReadmissionPredictionEngine:
    """Machine Learning model for readmission risk prediction"""
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        self.feature_importance = None
        self.metrics = None
        
    def prepare_features(self, patients_df):
        """Prepare features for ML model"""
        
        # Create feature matrix
        features = pd.DataFrame({
            'age': patients_df['age'],
            'gender_encoded': (patients_df['gender'] == 'Male').astype(int),
            'has_condition': (patients_df['condition'] != 'None').astype(int),
            'condition_severity': patients_df['condition'].map({
                'None': 0, 'Asthma': 1, 'Allergies': 1, 'Arthritis': 2,
                'Hypertension': 3, 'Diabetes': 3, 'Heart Disease': 4
            }).fillna(2),
            'insurance_encoded': patients_df['insurance_type'].map({
                'Private': 0, 'Medicare': 1, 'Medicaid': 2, 'Uninsured': 3
            }),
            'visits_per_year': patients_df['visits_per_year'],
            'avg_cost_normalized': (patients_df['avg_treatment_cost'] - patients_df['avg_treatment_cost'].mean()) / patients_df['avg_treatment_cost'].std(),
            'satisfaction_score': patients_df['satisfaction_score'],
            'prev_admissions': patients_df['prev_admissions'],
            'comorbidity_count': patients_df['comorbidity_count'],
            'emergency_ratio': patients_df['emergency_ratio'],
            'avg_los': patients_df['avg_length_of_stay'],
            'lab_abnormal': patients_df['lab_abnormality_rate']
        })
        
        target = patients_df['readmitted'].astype(int)
        
        return features, target
    
    def train(self, patients_df):
        """Train the prediction model"""
        
        X, y = self.prepare_features(patients_df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        self.metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'train_size': len(X_train),
            'test_size': len(X_test)
        }
        
        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return self.metrics
    
    def predict_risk(self, patients_df):
        """Predict readmission risk for patients"""
        
        X, _ = self.prepare_features(patients_df)
        
        # Get probability predictions
        risk_scores = self.model.predict_proba(X)[:, 1]
        
        # Classify risk levels
        risk_levels = pd.cut(risk_scores, 
                            bins=[0, 0.3, 0.6, 1.0],
                            labels=['Low', 'Medium', 'High'])
        
        return pd.DataFrame({
            'patient_id': patients_df['patient_id'],
            'risk_score': risk_scores.round(3),
            'risk_level': risk_levels
        })
    
    def get_high_risk_patients(self, patients_df, threshold=0.6):
        """Identify high-risk patients"""
        
        risk_df = self.predict_risk(patients_df)
        high_risk = risk_df[risk_df['risk_score'] >= threshold].merge(
            patients_df[['patient_id', 'age', 'condition', 'prev_admissions']], 
            on='patient_id'
        )
        
        return high_risk.sort_values('risk_score', ascending=False)


class HealthcareAnalytics:
    """Comprehensive analytics on healthcare data"""
    
    def __init__(self, patients_df, visits_df):
        self.patients = patients_df
        self.visits = visits_df
        self.merged = visits_df.merge(patients_df, on='patient_id')
    
    def demographic_analysis(self):
        """Analyze patient demographics"""
        return {
            'total_patients': len(self.patients),
            'avg_age': round(self.patients['age'].mean(), 1),
            'age_distribution': self.patients['age'].describe().to_dict(),
            'gender_breakdown': self.patients['gender'].value_counts().to_dict(),
            'condition_prevalence': self.patients['condition'].value_counts().to_dict(),
            'insurance_distribution': self.patients['insurance_type'].value_counts().to_dict()
        }
    
    def financial_analysis(self):
        """Analyze costs and revenue"""
        return {
            'total_revenue': round(self.visits['cost'].sum(), 2),
            'avg_visit_cost': round(self.visits['cost'].mean(), 2),
            'cost_by_visit_type': self.visits.groupby('visit_type')['cost'].agg(['mean', 'sum']).to_dict(),
            'cost_by_insurance': self.merged.groupby('insurance_type')['cost'].agg(['mean', 'count', 'sum']).to_dict(),
            'revenue_by_department': self.visits.groupby('department')['cost'].sum().to_dict()
        }
    
    def operational_analysis(self):
        """Analyze operations and efficiency"""
        return {
            'total_visits': len(self.visits),
            'visits_by_type': self.visits['visit_type'].value_counts().to_dict(),
            'avg_duration_by_type': self.visits.groupby('visit_type')['duration'].mean().to_dict(),
            'department_workload': self.visits['department'].value_counts().to_dict(),
            'monthly_visits': pd.to_datetime(self.visits['visit_date']).dt.to_period('M').value_counts().sort_index().to_dict()
        }
    
    def quality_analysis(self):
        """Analyze quality metrics"""
        readmission_rate = (self.patients['readmitted'].sum() / len(self.patients)) * 100
        
        return {
            'avg_satisfaction': round(self.patients['satisfaction_score'].mean(), 2),
            'satisfaction_by_condition': self.patients.groupby('condition')['satisfaction_score'].mean().to_dict(),
            'readmission_rate_percent': round(readmission_rate, 2),
            'readmissions_by_age_group': self.patients.groupby(pd.cut(self.patients['age'], 
                                                                       bins=[0, 30, 50, 70, 100]))['readmitted'].mean().to_dict(),
            'avg_comorbidity': round(self.patients['comorbidity_count'].mean(), 2),
            'high_los_patients': len(self.patients[self.patients['avg_length_of_stay'] > 7])
        }
    
    def predictive_insights(self):
        """Generate predictive insights"""
        
        # High-risk patients (multiple factors)
        high_risk = self.patients[
            (self.patients['age'] > 65) & 
            (self.patients['visits_per_year'] > 3) &
            (self.patients['condition'] != 'None')
        ]
        
        # Revenue opportunities
        low_satisfaction_high_value = self.patients[
            (self.patients['satisfaction_score'] < 6) &
            (self.patients['avg_treatment_cost'] > self.patients['avg_treatment_cost'].median())
        ]
        
        return {
            'high_risk_patients_count': len(high_risk),
            'high_risk_patient_ids': high_risk['patient_id'].tolist()[:10],
            'retention_risk_count': len(low_satisfaction_high_value),
            'cost_outliers': self.patients[
                self.patients['avg_treatment_cost'] > self.patients['avg_treatment_cost'].quantile(0.95)
            ]['patient_id'].tolist()[:10]
        }
    
    def generate_full_report(self):
        """Generate comprehensive analytics report"""
        return {
            'demographics': self.demographic_analysis(),
            'financial': self.financial_analysis(),
            'operations': self.operational_analysis(),
            'quality': self.quality_analysis(),
            'predictive': self.predictive_insights()
        }


# Generate data
print("="*80)
print("HEALTHCARE ANALYTICS & PREDICTION ENGINE")
print("="*80)
print("\n🔄 Generating synthetic healthcare data (7,000 patients)...")
generator = HealthcareDataGenerator(n_patients=7000)
patients_df = generator.generate_patients()
visits_df = generator.generate_visits(patients_df)

print(f"✅ Generated {len(patients_df)} patients and {len(visits_df)} visits")

# Save to CSV
patients_df.to_csv('patients.csv', index=False)
visits_df.to_csv('visits.csv', index=False)
print("✅ Data saved to patients.csv and visits.csv")

# Train prediction model
print("\n🤖 Training Readmission Prediction Model...")
print("-" * 80)
predictor = ReadmissionPredictionEngine()
metrics = predictor.train(patients_df)

print("\n📊 MODEL PERFORMANCE METRICS:")
print(f"  • Accuracy:  {metrics['accuracy']:.3f} ({metrics['accuracy']*100:.1f}%)")
print(f"  • Precision: {metrics['precision']:.3f}")
print(f"  • Recall:    {metrics['recall']:.3f}")
print(f"  • ROC-AUC:   {metrics['roc_auc']:.3f}")
print(f"  • Training Set: {metrics['train_size']} patients")
print(f"  • Test Set:     {metrics['test_size']} patients")

print("\n🎯 TOP 5 MOST IMPORTANT FEATURES:")
for idx, row in predictor.feature_importance.head(5).iterrows():
    print(f"  {idx+1}. {row['feature']:25} - {row['importance']:.4f}")

# Generate risk predictions
print("\n🔮 Generating Risk Predictions for All Patients...")
risk_predictions = predictor.predict_risk(patients_df)

# Risk distribution
risk_dist = risk_predictions['risk_level'].value_counts()
print("\n📈 RISK LEVEL DISTRIBUTION:")
for level in ['Low', 'Medium', 'High']:
    count = risk_dist.get(level, 0)
    pct = (count / len(risk_predictions)) * 100
    print(f"  • {level:8} Risk: {count:4} patients ({pct:5.1f}%)")

# High-risk patients
high_risk_patients = predictor.get_high_risk_patients(patients_df, threshold=0.6)
print(f"\n⚠️  IDENTIFIED {len(high_risk_patients)} HIGH-RISK PATIENTS (Risk Score ≥ 0.60)")
print("\nTop 10 Highest Risk Patients:")
print("-" * 80)
for idx, patient in high_risk_patients.head(10).iterrows():
    print(f"  {patient['patient_id']} | Risk: {patient['risk_score']:.3f} | "
          f"Age: {patient['age']} | Condition: {patient['condition']:15} | "
          f"Prev Admissions: {patient['prev_admissions']}")

# Save predictions
risk_predictions.to_csv('risk_predictions.csv', index=False)
high_risk_patients.to_csv('high_risk_patients.csv', index=False)
print("\n✅ Risk predictions saved to risk_predictions.csv")
print("✅ High-risk patients saved to high_risk_patients.csv")

# Run analytics
print("\n📊 Running Comprehensive Analytics...")
print("-" * 80)
analytics = HealthcareAnalytics(patients_df, visits_df)
report = analytics.generate_full_report()

# Add prediction metrics to report
report['prediction_model'] = {
    'metrics': metrics,
    'feature_importance': predictor.feature_importance.to_dict('records'),
    'risk_distribution': risk_dist.to_dict(),
    'high_risk_count': len(high_risk_patients),
    'high_risk_patients': high_risk_patients.head(20).to_dict('records')
}

# Save report
with open('analytics_report.json', 'w') as f:
    json.dump(report, f, indent=2, default=str)

print("\n" + "="*80)
print("COMPREHENSIVE ANALYTICS SUMMARY")
print("="*80)

print(f"\n📊 DEMOGRAPHICS")
print(f"  • Total Patients: {report['demographics']['total_patients']:,}")
print(f"  • Average Age: {report['demographics']['avg_age']} years")
print(f"  • Top Condition: {max(report['demographics']['condition_prevalence'], key=report['demographics']['condition_prevalence'].get)}")

print(f"\n💰 FINANCIAL")
print(f"  • Total Revenue: ${report['financial']['total_revenue']:,.2f}")
print(f"  • Average Visit Cost: ${report['financial']['avg_visit_cost']:,.2f}")

print(f"\n🏥 OPERATIONS")
print(f"  • Total Visits: {report['operations']['total_visits']:,}")
print(f"  • Most Common Visit: {max(report['operations']['visits_by_type'], key=report['operations']['visits_by_type'].get)}")

print(f"\n⭐ QUALITY METRICS")
print(f"  • Average Satisfaction: {report['quality']['avg_satisfaction']}/10")
print(f"  • Readmission Rate: {report['quality']['readmission_rate_percent']}%")
print(f"  • Average Comorbidity: {report['quality']['avg_comorbidity']}")

print(f"\n🔮 PREDICTIVE INSIGHTS")
print(f"  • Traditional High-Risk: {report['predictive']['high_risk_patients_count']} patients")
print(f"  • ML-Identified High-Risk: {len(high_risk_patients)} patients")
print(f"  • Model Accuracy: {metrics['accuracy']*100:.1f}%")
print(f"  • Retention Risk: {report['predictive']['retention_risk_count']} patients")

print("\n" + "="*80)
print("✅ ANALYSIS COMPLETE!")
print("="*80)
print("\nGenerated Files:")
print("  1. patients.csv - Patient demographic data (7,000 records)")
print("  2. visits.csv - Visit records")
print("  3. analytics_report.json - Full analytics report")
print("  4. risk_predictions.csv - ML risk scores for all patients")
print("  5. high_risk_patients.csv - High-risk patient list")
print("\n💡 Use these files with the dashboard for visualization!")
print("="*80)