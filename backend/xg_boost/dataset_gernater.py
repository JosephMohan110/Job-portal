import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Configuration
START_DATE = "2025-10-01"  # 3 months data
END_DATE = "2025-12-31"
KERALA_DISTRICTS = ["Thiruvananthapuram", "Ernakulam", "Kozhikode", "Thrissur", "Kannur"]
JOB_CATEGORIES = ["Plumber", "Electrician", "Carpenter", "Painter", "AC Technician"]
COMMISSION_RATE = 0.001  # 0.1%

def create_user_base():
    """Create initial user base with realistic distribution"""
    users = []
    user_id = 1000
    
    # Create 15 initial users (10 employees, 5 employers)
    for _ in range(10):  # Employees
        user_id += 1
        reg_date = (datetime.strptime(START_DATE, "%Y-%m-%d") - 
                   timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d')
        
        users.append({
            'user_id': user_id,
            'user_type': 'employee',
            'registration_date': reg_date,
            'district': random.choice(KERALA_DISTRICTS),
            'job_category': random.choice(JOB_CATEGORIES),
            'account_status': 'active',
            'deletion_date': None,
            'base_metrics': generate_base_metrics('employee', reg_date, START_DATE)
        })
    
    for _ in range(5):  # Employers
        user_id += 1
        reg_date = (datetime.strptime(START_DATE, "%Y-%m-%d") - 
                   timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d')
        
        users.append({
            'user_id': user_id,
            'user_type': 'employer',
            'registration_date': reg_date,
            'district': random.choice(KERALA_DISTRICTS),
            'job_category': None,
            'account_status': 'active',
            'deletion_date': None,
            'base_metrics': generate_base_metrics('employer', reg_date, START_DATE)
        })
    
    return users, user_id

def generate_base_metrics(user_type, reg_date, start_date):
    """Generate starting metrics based on registration date"""
    reg_datetime = datetime.strptime(reg_date, '%Y-%m-%d')
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    days_active_before_start = max(0, (start_datetime - reg_datetime).days)
    
    if user_type == 'employee':
        # Employees gain experience over time
        base_bookings = min(30, int(days_active_before_start * random.uniform(0.1, 0.3)))
        completed = int(base_bookings * random.uniform(0.85, 0.95))
        cancelled = base_bookings - completed
        total_earned = completed * random.randint(800, 3000)
        
        return {
            'total_bookings': base_bookings,
            'completed_bookings': completed,
            'cancelled_bookings': cancelled,
            'cancelled_within_3_days': int(cancelled * random.uniform(0.1, 0.3)),
            'total_earned': total_earned,
            'total_spent': 0,
            'platform_commission': total_earned * COMMISSION_RATE,
            'avg_rating': round(random.uniform(3.5, 5.0), 1) if completed > 0 else 0.0,
            'total_reviews': int(completed * random.uniform(0.7, 0.9)),
            'times_favorited': int(base_bookings * random.uniform(0.3, 0.7)),
            'certificates_uploaded': random.randint(0, 3)
        }
    else:  # employer
        base_bookings = min(15, int(days_active_before_start * random.uniform(0.05, 0.2)))
        completed = int(base_bookings * random.uniform(0.8, 0.9))
        cancelled = base_bookings - completed
        total_spent = completed * random.randint(1000, 4000)
        
        return {
            'total_bookings': base_bookings,
            'completed_bookings': completed,
            'cancelled_bookings': cancelled,
            'cancelled_within_3_days': int(cancelled * random.uniform(0.15, 0.35)),
            'total_earned': 0,
            'total_spent': total_spent,
            'platform_commission': total_spent * COMMISSION_RATE,
            'avg_rating': 0.0,
            'total_reviews': 0,
            'favorite_employee_count': random.randint(0, min(5, completed)),
            'times_favorited': 0,
            'certificates_uploaded': 0
        }

def simulate_daily_changes(users, current_date, next_user_id):
    """Simulate new signups and deletions for a day"""
    date_str = current_date.strftime('%Y-%m-%d')
    changes = {'new_signups': [], 'deletions': []}
    
    # NEW SIGNUPS - higher probability on weekdays
    if current_date.weekday() < 5:  # Weekday
        if random.random() < 0.2:  # 20% chance of new user (lower probability for smaller dataset)
            next_user_id += 1
            user_type = 'employee' if random.random() < 0.7 else 'employer'
            
            new_user = {
                'user_id': next_user_id,
                'user_type': user_type,
                'registration_date': date_str,
                'district': random.choice(KERALA_DISTRICTS),
                'job_category': random.choice(JOB_CATEGORIES) if user_type == 'employee' else None,
                'account_status': 'active',
                'deletion_date': None,
                'base_metrics': generate_base_metrics(user_type, date_str, date_str)  # Start with 0
            }
            users.append(new_user)
            changes['new_signups'].append(new_user)
    
    # ACCOUNT DELETIONS
    for user in users:
        if user['account_status'] == 'active' and user['deletion_date'] is None:
            # Higher chance if user has low activity
            deletion_prob = 0.001  # 0.1% daily base probability
            
            if user['user_type'] == 'employee':
                if user['base_metrics']['total_bookings'] == 0:
                    deletion_prob = 0.005  # 0.5% for inactive employees
            
            if random.random() < deletion_prob:
                user['account_status'] = 'deleted'
                user['deletion_date'] = date_str
                changes['deletions'].append(user)
    
    return users, next_user_id, changes

def update_metrics_daily(users, current_date):
    """Update metrics for each user daily"""
    for user in users:
        if user['account_status'] != 'active':
            continue
        
        # Skip if user registered today (no activity yet)
        if user['registration_date'] == current_date.strftime('%Y-%m-%d'):
            continue
        
        metrics = user['base_metrics']
        
        if user['user_type'] == 'employee':
            # Simulate daily work activity
            if random.random() < 0.5:  # 50% chance of getting work (higher for smaller set)
                new_bookings = random.randint(0, 2)
                metrics['total_bookings'] += new_bookings
                
                if new_bookings > 0:
                    completed = random.randint(0, new_bookings)
                    metrics['completed_bookings'] += completed
                    metrics['cancelled_bookings'] += (new_bookings - completed)
                    
                    if completed > 0:
                        earnings = completed * random.randint(800, 3000)
                        metrics['total_earned'] += earnings
                        metrics['platform_commission'] += earnings * COMMISSION_RATE
                        
                        # Update rating
                        old_rating = metrics['avg_rating']
                        old_completed = metrics['completed_bookings'] - completed
                        if old_completed > 0:
                            new_rating = random.uniform(3.5, 5.0)
                            metrics['avg_rating'] = round((old_rating * old_completed + new_rating * completed) / 
                                                         metrics['completed_bookings'], 1)
                        
                        metrics['total_reviews'] += int(completed * random.uniform(0.7, 0.9))
                        
                        if random.random() < 0.3:  # 30% chance of being favorited
                            metrics['times_favorited'] += random.randint(1, 2)
        
        else:  # employer
            if random.random() < 0.4:  # 40% chance of hiring (higher for smaller set)
                new_bookings = random.randint(0, 1)
                metrics['total_bookings'] += new_bookings
                
                if new_bookings > 0:
                    completed = random.randint(0, new_bookings)
                    metrics['completed_bookings'] += completed
                    metrics['cancelled_bookings'] += (new_bookings - completed)
                    
                    if completed > 0:
                        spending = completed * random.randint(1000, 4000)
                        metrics['total_spent'] += spending
                        metrics['platform_commission'] += spending * COMMISSION_RATE
                        
                        if random.random() < 0.2:  # 20% chance of favoriting
                            metrics['favorite_employee_count'] += 1
    
    return users

def generate_hourly_records_for_user(user, date):
    """Generate 24 hourly records for a user for a specific date"""
    records = []
    date_str = date.strftime('%Y-%m-%d')
    
    # Check if user exists on this date
    if user['registration_date'] > date_str:
        return records  # User not registered yet
    
    if (user['deletion_date'] and 
        datetime.strptime(user['deletion_date'], '%Y-%m-%d') < date):
        return records  # User already deleted
    
    metrics = user['base_metrics']
    
    for hour in range(24):
        timestamp = date.replace(hour=hour, minute=0, second=0)
        
        # Calculate days since registration
        reg_date = datetime.strptime(user['registration_date'], '%Y-%m-%d')
        days_since_reg = max(0, (date - reg_date).days)
        
        # Determine if active during this hour
        is_active = check_hourly_activity(hour, user['user_type'])
        
        # Calculate total amount in site (employee earnings + platform commission)
        total_amount_in_site = metrics['total_earned'] + metrics['platform_commission']
        
        # Create record
        if user['user_type'] == 'employee':
            record = {
                'timestamp': timestamp,
                'user_id': user['user_id'],
                'user_type': user['user_type'],
                'registration_date': user['registration_date'],
                'deletion_date': user['deletion_date'],
                'account_status': user['account_status'],
                'district': user['district'],
                'job_category': user['job_category'],
                'total_bookings': metrics['total_bookings'],
                'completed_bookings': metrics['completed_bookings'],
                'cancelled_bookings': metrics['cancelled_bookings'],
                'cancelled_within_3_days': metrics['cancelled_within_3_days'],
                'total_spent': 0.00,
                'total_earned': round(metrics['total_earned'], 2),
                'total_amount_in_site': round(total_amount_in_site, 2),  # NEW FEATURE
                'platform_commission': round(metrics['platform_commission'], 2),
                'avg_rating': metrics['avg_rating'],
                'total_reviews': metrics['total_reviews'],
                'favorite_employee_count': 0,
                'times_favorited': metrics['times_favorited'],
                'certificates_uploaded': metrics['certificates_uploaded'],
                'last_active': timestamp if is_active else (timestamp - timedelta(hours=random.randint(1, 24))),
                'active_during_hour': 1 if is_active else 0,
                'days_since_registration': days_since_reg,
                'is_new_user': 1 if days_since_reg <= 7 else 0,
                'is_deleted_user': 1 if user['account_status'] == 'deleted' and days_since_reg > 0 else 0
            }
        else:  # employer
            # For employers, total_amount_in_site is their total spent (money leaving site)
            employer_amount_in_site = metrics['total_spent']
            
            record = {
                'timestamp': timestamp,
                'user_id': user['user_id'],
                'user_type': user['user_type'],
                'registration_date': user['registration_date'],
                'deletion_date': user['deletion_date'],
                'account_status': user['account_status'],
                'district': user['district'],
                'job_category': None,
                'total_bookings': metrics['total_bookings'],
                'completed_bookings': metrics['completed_bookings'],
                'cancelled_bookings': metrics['cancelled_bookings'],
                'cancelled_within_3_days': metrics['cancelled_within_3_days'],
                'total_spent': round(metrics['total_spent'], 2),
                'total_earned': 0.00,
                'total_amount_in_site': round(employer_amount_in_site, 2),  # NEW FEATURE
                'platform_commission': round(metrics['platform_commission'], 2),
                'avg_rating': 0.0,
                'total_reviews': 0,
                'favorite_employee_count': metrics['favorite_employee_count'],
                'times_favorited': 0,
                'certificates_uploaded': 0,
                'last_active': timestamp if is_active else (timestamp - timedelta(hours=random.randint(1, 48))),
                'active_during_hour': 1 if is_active else 0,
                'days_since_registration': days_since_reg,
                'is_new_user': 1 if days_since_reg <= 7 else 0,
                'is_deleted_user': 1 if user['account_status'] == 'deleted' and days_since_reg > 0 else 0
            }
        
        records.append(record)
    
    return records

def check_hourly_activity(hour, user_type):
    """Determine if user is active during a specific hour"""
    # Peak hours: 8 AM - 12 PM, 5 PM - 9 PM
    is_peak = (8 <= hour <= 11) or (17 <= hour <= 20)
    
    if user_type == 'employee':
        if is_peak:
            return random.random() < 0.6  # 60% active during peak
        elif 6 <= hour <= 21:
            return random.random() < 0.3  # 30% active during day
        else:
            return random.random() < 0.1  # 10% active at night
    
    else:  # employer
        if is_peak:
            return random.random() < 0.7  # 70% active during peak
        elif 9 <= hour <= 17:
            return random.random() < 0.4  # 40% active during work hours
        else:
            return random.random() < 0.05  # 5% active outside hours

def generate_dataset():
    """Main function to generate the complete dataset"""
    print("Generating 3-month hourly dataset...")
    print("=" * 60)
    
    # Create initial users
    users, next_user_id = create_user_base()
    print(f"Initial users: {len(users)} (10 employees, 5 employers)")
    
    all_records = []
    daily_stats = []
    
    # Process each day
    current_date = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_date = datetime.strptime(END_DATE, "%Y-%m-%d")
    total_days = (end_date - current_date).days + 1
    
    day_count = 0
    while current_date <= end_date:
        day_count += 1
        
        # Daily user changes
        users, next_user_id, changes = simulate_daily_changes(users, current_date, next_user_id)
        
        # Update metrics
        users = update_metrics_daily(users, current_date)
        
        # Count active users
        active_users = [u for u in users 
                       if u['account_status'] == 'active' and
                       u['registration_date'] <= current_date.strftime('%Y-%m-%d') and
                       (u['deletion_date'] is None or 
                        datetime.strptime(u['deletion_date'], '%Y-%m-%d') >= current_date)]
        
        # Generate hourly records for each active user
        daily_records = 0
        for user in active_users:
            hourly_records = generate_hourly_records_for_user(user, current_date)
            all_records.extend(hourly_records)
            daily_records += len(hourly_records)
        
        # Track daily statistics
        daily_stats.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'active_users': len(active_users),
            'new_signups': len(changes['new_signups']),
            'deletions': len(changes['deletions']),
            'hourly_records': daily_records
        })
        
        # Progress update
        if day_count % 10 == 0:
            print(f"Day {day_count}/{total_days}: {len(active_users)} active users, {len(all_records):,} total records")
        
        current_date += timedelta(days=1)
    
    # Create DataFrame
    df = pd.DataFrame(all_records)
    
    # Add daily stats to each record
    stats_df = pd.DataFrame(daily_stats)
    df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    df = df.merge(stats_df, on='date', how='left')
    
    # Optimize data types
    df['user_id'] = df['user_id'].astype('int32')
    df['active_during_hour'] = df['active_during_hour'].astype('int8')
    df['is_new_user'] = df['is_new_user'].astype('int8')
    df['is_deleted_user'] = df['is_deleted_user'].astype('int8')
    df['days_since_registration'] = df['days_since_registration'].astype('int16')
    df['active_users'] = df['active_users'].astype('int16')
    df['new_signups'] = df['new_signups'].astype('int8')
    df['deletions'] = df['deletions'].astype('int8')
    df['hourly_records'] = df['hourly_records'].astype('int16')
    
    return df, users

def save_dataset(df, filename="beiner_hourly_dataset_small.csv"):
    """Save dataset to CSV"""
    print(f"\nSaving dataset to {filename}...")
    df.to_csv(filename, index=False)
    
    # Calculate file size
    import os
    file_size = os.path.getsize(filename) / 1024 / 1024
    print(f"File size: {file_size:.2f} MB")
    
    return filename

def print_summary(df, users):
    """Print comprehensive summary"""
    print("\n" + "=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)
    print(f"Time period: {START_DATE} to {END_DATE}")
    print(f"Total records: {len(df):,}")
    print(f"Total users in system: {len(users)}")
    print(f"Unique users in dataset: {df['user_id'].nunique()}")
    
    print(f"\nUser Type Distribution:")
    user_type_counts = df[['user_id', 'user_type']].drop_duplicates()['user_type'].value_counts()
    print(user_type_counts)
    
    print(f"\nAccount Status Distribution:")
    status_counts = df[['user_id', 'account_status']].drop_duplicates()['account_status'].value_counts()
    print(status_counts)
    
    print(f"\nActivity Statistics:")
    print(f"Total active hours: {df['active_during_hour'].sum():,}")
    print(f"Overall activity rate: {df['active_during_hour'].mean()*100:.1f}%")
    
    print(f"\nEmployee Statistics:")
    emp_df = df[df['user_type'] == 'employee']
    print(f"Number of employees: {emp_df['user_id'].nunique()}")
    print(f"Average bookings per employee: {emp_df['total_bookings'].mean():.1f}")
    print(f"Average earnings per employee: ₹{emp_df['total_earned'].mean():,.0f}")
    print(f"Average rating: {emp_df['avg_rating'].mean():.2f}")
    
    print(f"\nEmployer Statistics:")
    emp_df = df[df['user_type'] == 'employer']
    print(f"Number of employers: {emp_df['user_id'].nunique()}")
    print(f"Average bookings per employer: {emp_df['total_bookings'].mean():.1f}")
    print(f"Average spending per employer: ₹{emp_df['total_spent'].mean():,.0f}")
    
    print(f"\nFinancial Summary:")
    print(f"Total platform commission: ₹{df['platform_commission'].sum():,.2f}")
    total_employee_earned = df[df['user_type']=='employee']['total_earned'].sum()
    print(f"Total earned by employees: ₹{total_employee_earned:,.2f}")
    total_employer_spent = df[df['user_type']=='employer']['total_spent'].sum()
    print(f"Total spent by employers: ₹{total_employer_spent:,.2f}")
    
    # Calculate overall site amount
    total_amount_in_site = df['total_amount_in_site'].sum() / len(df['date'].unique())
    print(f"Average daily amount in site: ₹{total_amount_in_site:,.2f}")
    
    print(f"\nLifecycle Metrics:")
    print(f"New users (registered ≤7 days): {df['is_new_user'].sum():,} records")
    print(f"Deleted users: {df['is_deleted_user'].sum():,} records")
    
    # Show sample of data
    print("\n" + "=" * 60)
    print("DATA STRUCTURE (first 24 rows of user 1001)")
    print("=" * 60)
    sample_user = df[df['user_id'] == 1001].head(24)
    print(f"User 1001 has {len(df[df['user_id'] == 1001]):,} hourly records")
    print(f"Showing first day (24 hours):")
    print(sample_user[['timestamp', 'active_during_hour', 'total_bookings', 'total_earned', 'total_amount_in_site', 'days_since_registration']].to_string())

def main():
    """Main execution"""
    print("BEINER PLATFORM - 3 MONTH HOURLY DATASET")
    print("=" * 60)
    print("Structure: Each user has 24 rows per day (one per hour)")
    print(f"Timeframe: {START_DATE} to {END_DATE} (3 months)")
    print("Initial Users: 10 employees and 5 employers")
    print("=" * 60)
    
    try:
        # Generate dataset
        df, users = generate_dataset()
        
        # Save dataset
        filename = save_dataset(df)
        
        # Print summary
        print_summary(df, users)
        
        print(f"\nDataset saved as: {filename}")
        print("\nColumns in dataset:")
        for i, col in enumerate(df.columns.tolist(), 1):
            print(f"{i:2}. {col}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()