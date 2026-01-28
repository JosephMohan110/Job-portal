import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import List, Dict, Tuple

# Configuration
START_DATE = "2025-10-01"
END_DATE = "2025-12-31"
KERALA_DISTRICTS = ["Thiruvananthapuram", "Ernakulam", "Kozhikode", "Thrissur", "Kannur"]
JOB_CATEGORIES = ["Plumber", "Electrician", "Carpenter", "Painter", "AC Technician"]
COMMISSION_RATE = 0.001  # 0.1%

class BeinerUser:
    """Class to represent a user with their metrics and behavior"""
    
    def __init__(self, user_id: int, user_type: str, registration_date: str, 
                 district: str, job_category: str = None):
        self.user_id = user_id
        self.user_type = user_type
        self.registration_date = registration_date
        self.district = district
        self.job_category = job_category
        self.account_status = 'active'
        self.deletion_date = None
        
        # Daily metrics that change over time
        self.daily_metrics = {
            'date': None,
            'total_bookings': 0,
            'completed_bookings': 0,
            'cancelled_bookings': 0,
            'cancelled_within_3_days': 0,
            'total_earned': 0.0,  # For employees
            'total_spent': 0.0,   # For employers
            'platform_commission': 0.0,
            'avg_rating': 0.0,
            'total_reviews': 0,
            'favorite_employee_count': 0,
            'times_favorited': 0,
            'certificates_uploaded': 0,
            'daily_active_minutes': 0,
            'sessions_count': 0,
            'profile_views': 0,
            'messages_sent': 0,
            'job_applications': 0,
            'jobs_posted': 0,
            'contracts_signed': 0,
            'payment_disputes': 0,
            'support_tickets': 0,
            'is_active_today': 0,
            'streak_days': 0,
            'last_active_date': None
        }
        
        # Initialize base metrics based on registration date
        self._initialize_base_metrics(registration_date)
    
    def _initialize_base_metrics(self, reg_date: str):
        """Initialize metrics based on registration date"""
        reg_datetime = datetime.strptime(reg_date, '%Y-%m-%d')
        start_datetime = datetime.strptime(START_DATE, '%Y-%m-%d')
        days_active_before_start = max(0, (start_datetime - reg_datetime).days)
        
        if self.user_type == 'employee':
            # Employees gain experience over time
            base_bookings = min(30, int(days_active_before_start * random.uniform(0.1, 0.3)))
            self.daily_metrics['total_bookings'] = base_bookings
            self.daily_metrics['completed_bookings'] = int(base_bookings * random.uniform(0.85, 0.95))
            self.daily_metrics['cancelled_bookings'] = base_bookings - self.daily_metrics['completed_bookings']
            self.daily_metrics['cancelled_within_3_days'] = int(self.daily_metrics['cancelled_bookings'] * random.uniform(0.1, 0.3))
            self.daily_metrics['total_earned'] = self.daily_metrics['completed_bookings'] * random.randint(800, 3000)
            self.daily_metrics['platform_commission'] = self.daily_metrics['total_earned'] * COMMISSION_RATE
            self.daily_metrics['avg_rating'] = round(random.uniform(3.5, 5.0), 1) if self.daily_metrics['completed_bookings'] > 0 else 0.0
            self.daily_metrics['total_reviews'] = int(self.daily_metrics['completed_bookings'] * random.uniform(0.7, 0.9))
            self.daily_metrics['times_favorited'] = int(base_bookings * random.uniform(0.3, 0.7))
            self.daily_metrics['certificates_uploaded'] = random.randint(0, 3)
            self.daily_metrics['contracts_signed'] = self.daily_metrics['completed_bookings']
            
        else:  # employer
            base_bookings = min(15, int(days_active_before_start * random.uniform(0.05, 0.2)))
            self.daily_metrics['total_bookings'] = base_bookings
            self.daily_metrics['completed_bookings'] = int(base_bookings * random.uniform(0.8, 0.9))
            self.daily_metrics['cancelled_bookings'] = base_bookings - self.daily_metrics['completed_bookings']
            self.daily_metrics['cancelled_within_3_days'] = int(self.daily_metrics['cancelled_bookings'] * random.uniform(0.15, 0.35))
            self.daily_metrics['total_spent'] = self.daily_metrics['completed_bookings'] * random.randint(1000, 4000)
            self.daily_metrics['platform_commission'] = self.daily_metrics['total_spent'] * COMMISSION_RATE
            self.daily_metrics['favorite_employee_count'] = random.randint(0, min(5, self.daily_metrics['completed_bookings']))
            self.daily_metrics['contracts_signed'] = self.daily_metrics['completed_bookings']
    
    def update_daily_activity(self, date: datetime):
        """Update user's daily activity metrics"""
        date_str = date.strftime('%Y-%m-%d')
        self.daily_metrics['date'] = date_str
        
        # Reset daily-specific metrics
        daily_reset_metrics = ['daily_active_minutes', 'sessions_count', 'profile_views', 
                              'messages_sent', 'job_applications', 'jobs_posted', 
                              'is_active_today', 'payment_disputes', 'support_tickets']
        for metric in daily_reset_metrics:
            self.daily_metrics[metric] = 0
        
        # Check if user is active today
        if self.account_status != 'active':
            self.daily_metrics['is_active_today'] = 0
            self.daily_metrics['streak_days'] = 0
            return
        
        # Determine if active today (based on user type and day of week)
        is_weekday = date.weekday() < 5
        activity_prob = 0.7 if is_weekday else 0.4  # Higher activity on weekdays
        
        if random.random() < activity_prob:
            self.daily_metrics['is_active_today'] = 1
            self.daily_metrics['streak_days'] += 1
            self.daily_metrics['last_active_date'] = date_str
            
            # Generate daily activity metrics
            self._generate_daily_engagement()
            
            # Generate business transactions
            self._generate_daily_transactions(date)
        else:
            self.daily_metrics['is_active_today'] = 0
            self.daily_metrics['streak_days'] = 0
    
    def _generate_daily_engagement(self):
        """Generate daily engagement metrics"""
        # Daily active minutes (normally distributed around typical usage)
        if self.user_type == 'employee':
            self.daily_metrics['daily_active_minutes'] = int(random.normalvariate(45, 15))
            self.daily_metrics['sessions_count'] = random.randint(1, 5)
            self.daily_metrics['profile_views'] = random.randint(0, 10)
            self.daily_metrics['messages_sent'] = random.randint(0, 8)
            self.daily_metrics['job_applications'] = random.randint(0, 3)
        else:  # employer
            self.daily_metrics['daily_active_minutes'] = int(random.normalvariate(30, 10))
            self.daily_metrics['sessions_count'] = random.randint(1, 3)
            self.daily_metrics['profile_views'] = random.randint(0, 15)
            self.daily_metrics['messages_sent'] = random.randint(0, 12)
            self.daily_metrics['jobs_posted'] = random.randint(0, 2)
        
        # Occasionally generate support issues
        if random.random() < 0.02:  # 2% chance daily
            self.daily_metrics['support_tickets'] = random.randint(1, 2)
        
        if random.random() < 0.01:  # 1% chance daily
            self.daily_metrics['payment_disputes'] = 1
    
    def _generate_daily_transactions(self, date: datetime):
        """Generate daily business transactions"""
        date_str = date.strftime('%Y-%m-%d')
        
        # Skip if user registered today
        if self.registration_date == date_str:
            return
        
        if self.user_type == 'employee':
            # Employee gets work
            if random.random() < 0.3:  # 30% chance of getting work daily
                new_bookings = random.randint(0, 2)
                self.daily_metrics['total_bookings'] += new_bookings
                
                if new_bookings > 0:
                    completed = random.randint(0, new_bookings)
                    self.daily_metrics['completed_bookings'] += completed
                    self.daily_metrics['cancelled_bookings'] += (new_bookings - completed)
                    
                    # Track cancellations within 3 days
                    new_cancellations = new_bookings - completed
                    if new_cancellations > 0 and random.random() < 0.2:
                        self.daily_metrics['cancelled_within_3_days'] += random.randint(0, new_cancellations)
                    
                    if completed > 0:
                        earnings = completed * random.randint(800, 3000)
                        self.daily_metrics['total_earned'] += earnings
                        self.daily_metrics['platform_commission'] += earnings * COMMISSION_RATE
                        self.daily_metrics['contracts_signed'] += completed
                        
                        # Update rating (weighted average)
                        old_rating = self.daily_metrics['avg_rating']
                        old_completed = self.daily_metrics['completed_bookings'] - completed
                        if old_completed > 0:
                            new_rating = random.uniform(3.5, 5.0)
                            total_completed = self.daily_metrics['completed_bookings']
                            self.daily_metrics['avg_rating'] = round(
                                (old_rating * old_completed + new_rating * completed) / total_completed, 1
                            )
                        
                        # Generate reviews
                        self.daily_metrics['total_reviews'] += int(completed * random.uniform(0.7, 0.9))
                        
                        # Chance of being favorited
                        if random.random() < 0.2:  # 20% chance per completed job
                            self.daily_metrics['times_favorited'] += random.randint(1, 2)
        
        else:  # employer
            # Employer hires workers
            if random.random() < 0.25:  # 25% chance of hiring daily
                new_bookings = random.randint(0, 1)
                self.daily_metrics['total_bookings'] += new_bookings
                
                if new_bookings > 0:
                    completed = random.randint(0, new_bookings)
                    self.daily_metrics['completed_bookings'] += completed
                    self.daily_metrics['cancelled_bookings'] += (new_bookings - completed)
                    
                    # Track cancellations within 3 days
                    new_cancellations = new_bookings - completed
                    if new_cancellations > 0 and random.random() < 0.3:
                        self.daily_metrics['cancelled_within_3_days'] += random.randint(0, new_cancellations)
                    
                    if completed > 0:
                        spending = completed * random.randint(1000, 4000)
                        self.daily_metrics['total_spent'] += spending
                        self.daily_metrics['platform_commission'] += spending * COMMISSION_RATE
                        self.daily_metrics['contracts_signed'] += completed
                        
                        # Chance of favoriting an employee
                        if random.random() < 0.15:  # 15% chance per completed job
                            self.daily_metrics['favorite_employee_count'] += 1
    
    def to_daily_record(self) -> Dict:
        """Convert user to daily record dictionary"""
        record = {
            'date': self.daily_metrics['date'],
            'user_id': self.user_id,
            'user_type': self.user_type,
            'registration_date': self.registration_date,
            'deletion_date': self.deletion_date,
            'account_status': self.account_status,
            'district': self.district,
            'job_category': self.job_category,
            'total_bookings': self.daily_metrics['total_bookings'],
            'completed_bookings': self.daily_metrics['completed_bookings'],
            'cancelled_bookings': self.daily_metrics['cancelled_bookings'],
            'cancelled_within_3_days': self.daily_metrics['cancelled_within_3_days'],
            'total_spent': round(self.daily_metrics['total_spent'], 2),
            'total_earned': round(self.daily_metrics['total_earned'], 2),
            'platform_commission': round(self.daily_metrics['platform_commission'], 2),
            'avg_rating': self.daily_metrics['avg_rating'],
            'total_reviews': self.daily_metrics['total_reviews'],
            'favorite_employee_count': self.daily_metrics['favorite_employee_count'],
            'times_favorited': self.daily_metrics['times_favorited'],
            'certificates_uploaded': self.daily_metrics['certificates_uploaded'],
            'daily_active_minutes': self.daily_metrics['daily_active_minutes'],
            'sessions_count': self.daily_metrics['sessions_count'],
            'profile_views': self.daily_metrics['profile_views'],
            'messages_sent': self.daily_metrics['messages_sent'],
            'job_applications': self.daily_metrics['job_applications'],
            'jobs_posted': self.daily_metrics['jobs_posted'],
            'contracts_signed': self.daily_metrics['contracts_signed'],
            'payment_disputes': self.daily_metrics['payment_disputes'],
            'support_tickets': self.daily_metrics['support_tickets'],
            'is_active_today': self.daily_metrics['is_active_today'],
            'streak_days': self.daily_metrics['streak_days'],
            'last_active_date': self.daily_metrics['last_active_date'],
            'days_since_registration': 0,  # Will be calculated later
            'is_new_user': 0,  # Will be calculated later
            'is_deleted_user': 1 if self.account_status == 'deleted' else 0
        }
        
        # Calculate derived metrics
        if self.registration_date:
            reg_date = datetime.strptime(self.registration_date, '%Y-%m-%d')
            current_date = datetime.strptime(self.daily_metrics['date'], '%Y-%m-%d')
            days_since_reg = max(0, (current_date - reg_date).days)
            record['days_since_registration'] = days_since_reg
            record['is_new_user'] = 1 if days_since_reg <= 7 else 0
        
        # Calculate success rate
        if record['total_bookings'] > 0:
            record['success_rate'] = round(record['completed_bookings'] / record['total_bookings'] * 100, 2)
        else:
            record['success_rate'] = 0.0
        
        # Calculate total amount in platform
        if self.user_type == 'employee':
            record['total_amount_in_site'] = round(record['total_earned'] + record['platform_commission'], 2)
        else:
            record['total_amount_in_site'] = round(record['total_spent'], 2)
        
        # Calculate average earnings per completed job
        if record['completed_bookings'] > 0:
            if self.user_type == 'employee':
                record['avg_earning_per_job'] = round(record['total_earned'] / record['completed_bookings'], 2)
            else:
                record['avg_spending_per_job'] = round(record['total_spent'] / record['completed_bookings'], 2)
        else:
            if self.user_type == 'employee':
                record['avg_earning_per_job'] = 0.0
            else:
                record['avg_spending_per_job'] = 0.0
        
        return record

def create_initial_users() -> Tuple[List[BeinerUser], int]:
    """Create initial user base"""
    users = []
    user_id = 1000
    
    # Create 15 initial users (10 employees, 5 employers)
    for _ in range(10):  # Employees
        user_id += 1
        reg_date = (datetime.strptime(START_DATE, "%Y-%m-%d") - 
                   timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d')
        
        user = BeinerUser(
            user_id=user_id,
            user_type='employee',
            registration_date=reg_date,
            district=random.choice(KERALA_DISTRICTS),
            job_category=random.choice(JOB_CATEGORIES)
        )
        users.append(user)
    
    for _ in range(5):  # Employers
        user_id += 1
        reg_date = (datetime.strptime(START_DATE, "%Y-%m-%d") - 
                   timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d')
        
        user = BeinerUser(
            user_id=user_id,
            user_type='employer',
            registration_date=reg_date,
            district=random.choice(KERALA_DISTRICTS),
            job_category=None
        )
        users.append(user)
    
    return users, user_id

def simulate_daily_signups_deletions(users: List[BeinerUser], current_date: datetime, 
                                    next_user_id: int) -> Tuple[List[BeinerUser], int, Dict]:
    """Simulate daily new signups and account deletions"""
    changes = {'new_signups': [], 'deletions': []}
    date_str = current_date.strftime('%Y-%m-%d')
    
    # NEW SIGNUPS
    if current_date.weekday() < 5:  # Higher on weekdays
        signup_prob = 0.25  # 25% chance of new signup
        
        # Adjust based on platform growth (more signups over time)
        days_since_start = (current_date - datetime.strptime(START_DATE, "%Y-%m-%d")).days
        if days_since_start > 45:  # After 1.5 months
            signup_prob = 0.3
        
        if random.random() < signup_prob:
            next_user_id += 1
            user_type = 'employee' if random.random() < 0.7 else 'employer'
            
            new_user = BeinerUser(
                user_id=next_user_id,
                user_type=user_type,
                registration_date=date_str,
                district=random.choice(KERALA_DISTRICTS),
                job_category=random.choice(JOB_CATEGORIES) if user_type == 'employee' else None
            )
            users.append(new_user)
            changes['new_signups'].append(new_user)
    
    # ACCOUNT DELETIONS
    for user in users:
        if user.account_status == 'active':
            deletion_prob = 0.001  # 0.1% daily base probability
            
            # Higher deletion probability for inactive users
            if user.user_type == 'employee':
                if user.daily_metrics['total_bookings'] == 0:
                    # Inactive employee for long time
                    reg_date = datetime.strptime(user.registration_date, '%Y-%m-%d')
                    days_since_reg = (current_date - reg_date).days
                    if days_since_reg > 30 and user.daily_metrics['streak_days'] == 0:
                        deletion_prob = 0.005
            else:  # employer
                if user.daily_metrics['total_bookings'] == 0:
                    reg_date = datetime.strptime(user.registration_date, '%Y-%m-%d')
                    days_since_reg = (current_date - reg_date).days
                    if days_since_reg > 60 and user.daily_metrics['streak_days'] == 0:
                        deletion_prob = 0.003
            
            if random.random() < deletion_prob:
                user.account_status = 'deleted'
                user.deletion_date = date_str
                changes['deletions'].append(user)
    
    return users, next_user_id, changes

def generate_daily_dataset():
    """Generate complete daily dataset"""
    print("Generating 3-month daily dataset...")
    print("=" * 60)
    
    # Initialize
    users, next_user_id = create_initial_users()
    print(f"Initial users: {len(users)} (10 employees, 5 employers)")
    
    all_records = []
    platform_daily_stats = []
    
    # Process each day
    current_date = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_date = datetime.strptime(END_DATE, "%Y-%m-%d")
    total_days = (end_date - current_date).days + 1
    
    day_count = 0
    while current_date <= end_date:
        day_count += 1
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Daily user changes
        users, next_user_id, changes = simulate_daily_signups_deletions(
            users, current_date, next_user_id
        )
        
        # Generate daily records for each user who exists on this date
        daily_records = []
        daily_active_users = 0
        
        for user in users:
            # Skip users not yet registered
            if user.registration_date > date_str:
                continue
            
            # Skip deleted users before their deletion date
            if (user.deletion_date and 
                datetime.strptime(user.deletion_date, '%Y-%m-%d') < current_date):
                continue
            
            # Update user's daily activity
            user.update_daily_activity(current_date)
            
            # Get daily record
            record = user.to_daily_record()
            
            # Add platform-level metrics
            active_users_today = sum(1 for u in users 
                                   if u.registration_date <= date_str and 
                                   (not u.deletion_date or 
                                    datetime.strptime(u.deletion_date, '%Y-%m-%d') >= current_date) and
                                   u.daily_metrics['is_active_today'] == 1)
            
            record['platform_active_users'] = active_users_today
            record['platform_new_signups'] = len(changes['new_signups'])
            record['platform_deletions'] = len(changes['deletions'])
            
            daily_records.append(record)
            
            if user.daily_metrics['is_active_today'] == 1:
                daily_active_users += 1
        
        # Add daily platform statistics
        platform_stats = {
            'date': date_str,
            'total_users': len([u for u in users if u.registration_date <= date_str]),
            'active_users': daily_active_users,
            'new_signups': len(changes['new_signups']),
            'deletions': len(changes['deletions']),
            'total_employees': len([u for u in users if u.user_type == 'employee' and 
                                   u.registration_date <= date_str]),
            'total_employers': len([u for u in users if u.user_type == 'employer' and 
                                   u.registration_date <= date_str]),
            'total_bookings_today': sum(r['total_bookings'] - 
                                       user.daily_metrics['total_bookings'] + 
                                       (r['total_bookings'] if 'total_bookings' in user.daily_metrics else 0) 
                                       for r, user in zip(daily_records, users) if user.registration_date <= date_str),
            'total_transaction_value': sum(r['total_earned'] + r['total_spent'] for r in daily_records),
            'total_commission': sum(r['platform_commission'] for r in daily_records)
        }
        platform_daily_stats.append(platform_stats)
        
        all_records.extend(daily_records)
        
        # Progress update
        if day_count % 10 == 0:
            print(f"Day {day_count}/{total_days}: {daily_active_users} active users, {len(all_records):,} total records")
        
        current_date += timedelta(days=1)
    
    # Create DataFrame
    df = pd.DataFrame(all_records)
    
    # Add platform stats to each record
    stats_df = pd.DataFrame(platform_daily_stats)
    df = df.merge(stats_df, on='date', how='left')
    
    # Optimize data types
    df = optimize_data_types(df)
    
    # Sort by date and user_id
    df = df.sort_values(['date', 'user_id']).reset_index(drop=True)
    
    return df, users

def optimize_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame data types for memory efficiency"""
    # Integer columns
    int_columns = ['user_id', 'total_bookings', 'completed_bookings', 'cancelled_bookings',
                  'cancelled_within_3_days', 'total_reviews', 'favorite_employee_count',
                  'times_favorited', 'certificates_uploaded', 'sessions_count',
                  'profile_views', 'messages_sent', 'job_applications', 'jobs_posted',
                  'contracts_signed', 'payment_disputes', 'support_tickets',
                  'is_active_today', 'streak_days', 'days_since_registration',
                  'is_new_user', 'is_deleted_user', 'platform_active_users',
                  'platform_new_signups', 'platform_deletions', 'total_users',
                  'active_users', 'total_employees', 'total_employers']
    
    for col in int_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')
    
    # Float columns
    float_columns = ['total_spent', 'total_earned', 'platform_commission', 
                     'avg_rating', 'success_rate', 'total_amount_in_site',
                     'avg_earning_per_job', 'avg_spending_per_job',
                     'total_transaction_value', 'total_commission']
    
    for col in float_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
    
    # Categorical columns
    cat_columns = ['user_type', 'account_status', 'district', 'job_category']
    for col in cat_columns:
        if col in df.columns:
            df[col] = df[col].astype('category')
    
    # Datetime columns
    date_columns = ['date', 'registration_date', 'deletion_date', 'last_active_date']
    for col in date_columns:
        if col in df.columns and df[col].notna().any():
            df[col] = pd.to_datetime(df[col])
    
    return df

def save_dataset(df: pd.DataFrame, filename: str = "beiner_daily_dataset.csv"):
    """Save dataset to CSV"""
    print(f"\nSaving dataset to {filename}...")
    df.to_csv(filename, index=False)
    
    # Calculate file size
    import os
    file_size = os.path.getsize(filename) / 1024 / 1024
    print(f"File size: {file_size:.2f} MB")
    
    return filename

def print_detailed_summary(df: pd.DataFrame, users: List[BeinerUser]):
    """Print comprehensive dataset summary"""
    print("\n" + "=" * 60)
    print("DAILY DATASET SUMMARY")
    print("=" * 60)
    print(f"Time period: {START_DATE} to {END_DATE}")
    print(f"Total daily records: {len(df):,}")
    print(f"Total unique days: {df['date'].nunique()}")
    print(f"Total users in system: {len(users)}")
    print(f"Unique users in dataset: {df['user_id'].nunique()}")
    
    print(f"\nUser Type Distribution:")
    user_summary = df[['user_id', 'user_type']].drop_duplicates()['user_type'].value_counts()
    for user_type, count in user_summary.items():
        print(f"  {user_type}: {count} users ({count/len(df['user_id'].unique())*100:.1f}%)")
    
    print(f"\nAccount Status Distribution:")
    status_summary = df[['user_id', 'account_status']].drop_duplicates()['account_status'].value_counts()
    for status, count in status_summary.items():
        print(f"  {status}: {count} users")
    
    print(f"\nPlatform Growth Statistics:")
    print(f"Average daily active users: {df['platform_active_users'].mean():.1f}")
    print(f"Peak daily active users: {df['platform_active_users'].max()}")
    print(f"Total new signups: {df['platform_new_signups'].sum()}")
    print(f"Total account deletions: {df['platform_deletions'].sum()}")
    
    print(f"\nEmployee Statistics:")
    emp_df = df[df['user_type'] == 'employee']
    print(f"Number of employees: {emp_df['user_id'].nunique()}")
    print(f"Average bookings per employee: {emp_df['total_bookings'].mean():.1f}")
    print(f"Average completed bookings per employee: {emp_df['completed_bookings'].mean():.1f}")
    print(f"Average earnings per employee: ₹{emp_df['total_earned'].mean():,.0f}")
    print(f"Average rating: {emp_df['avg_rating'].mean():.2f}")
    print(f"Average success rate: {emp_df['success_rate'].mean():.1f}%")
    
    print(f"\nEmployer Statistics:")
    empr_df = df[df['user_type'] == 'employer']
    print(f"Number of employers: {empr_df['user_id'].nunique()}")
    print(f"Average bookings per employer: {empr_df['total_bookings'].mean():.1f}")
    print(f"Average spending per employer: ₹{empr_df['total_spent'].mean():,.0f}")
    print(f"Average favorite employees: {empr_df['favorite_employee_count'].mean():.1f}")
    
    print(f"\nEngagement Metrics:")
    print(f"Average daily active minutes: {df['daily_active_minutes'].mean():.1f}")
    print(f"Average sessions per day: {df['sessions_count'].mean():.1f}")
    print(f"Overall activity rate: {df['is_active_today'].mean()*100:.1f}%")
    print(f"Average streak days: {df['streak_days'].mean():.1f}")
    
    print(f"\nFinancial Summary:")
    print(f"Total platform commission: ₹{df['platform_commission'].sum():,.2f}")
    total_employee_earned = emp_df['total_earned'].sum()
    print(f"Total earned by employees: ₹{total_employee_earned:,.2f}")
    total_employer_spent = empr_df['total_spent'].sum()
    print(f"Total spent by employers: ₹{total_employer_spent:,.2f}")
    print(f"Total transaction value: ₹{df['total_transaction_value'].sum():,.2f}")
    
    # Show sample data structure
    print("\n" + "=" * 60)
    print("SAMPLE DATA (first 5 days for user 1001)")
    print("=" * 60)
    sample_user = df[df['user_id'] == 1001].head()
    print(sample_user[['date', 'user_type', 'district', 'job_category', 
                      'total_bookings', 'completed_bookings', 'total_earned', 
                      'avg_rating', 'is_active_today', 'streak_days']].to_string())

def main():
    """Main execution"""
    print("BEINER PLATFORM - 3 MONTH DAILY DATASET")
    print("=" * 60)
    print("Structure: Each user has one row per day")
    print(f"Timeframe: {START_DATE} to {END_DATE} (3 months)")
    print("Initial Users: 10 employees and 5 employers")
    print("Features: 40+ metrics including activity, transactions, and platform stats")
    print("=" * 60)
    
    try:
        # Generate dataset
        df, users = generate_daily_dataset()
        
        # Save dataset
        filename = save_dataset(df, "beiner_daily_dataset_detailed.csv")
        
        # Print summary
        print_detailed_summary(df, users)
        
        print(f"\nDataset saved as: {filename}")
        print(f"\nDataset shape: {df.shape[0]} rows × {df.shape[1]} columns")
        
        print("\nColumns in dataset:")
        columns = df.columns.tolist()
        for i in range(0, len(columns), 4):
            print("  " + "  ".join(f"{col:25}" for col in columns[i:i+4]))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()