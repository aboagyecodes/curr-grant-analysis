"""
Grant Impact Analysis Engine

Analyzes the impact of IMF/World Bank grants on currency valuation,
accounting for commodity price influences.
"""

import pandas as pd
import numpy as np
from datetime import timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import IMPACT_SCORE_WEIGHTS


class GrantImpactAnalyzer:
    """Analyzes grant impact on currency movements"""
    
    def __init__(self, fx_data, commodity_data, grants_data):
        """
        Initialize analyzer
        
        Args:
            fx_data: DataFrame with date, rate, currency columns
            commodity_data: dict of {commodity_name: DataFrame}
            grants_data: DataFrame with standardized grant data
        """
        self.fx_data = fx_data.copy()
        self.commodity_data = commodity_data
        self.grants_data = grants_data.copy()
        
        # Ensure dates are datetime
        self.fx_data['date'] = pd.to_datetime(self.fx_data['date'])
        self.grants_data['disbursement_date'] = pd.to_datetime(self.grants_data['disbursement_date'])
    
    def calculate_pre_trend(self, grant_date, window_weeks=4):
        """
        Calculate currency trend before grant disbursement
        
        Args:
            grant_date: Date of grant disbursement
            window_weeks: Number of weeks to look back
        
        Returns:
            dict: {
                'avg_rate': float,
                'trend_direction': 'up'/'down'/'stable',
                'volatility': float,
                'change_percent': float
            }
        """
        start_date = grant_date - timedelta(weeks=window_weeks)
        
        # Filter FX data for pre-period
        mask = (self.fx_data['date'] >= start_date) & (self.fx_data['date'] < grant_date)
        pre_data = self.fx_data[mask].copy()
        
        if len(pre_data) < 2:
            return {
                'avg_rate': 0,
                'trend_direction': 'unknown',
                'volatility': 0,
                'change_percent': 0
            }
        
        # Calculate metrics
        avg_rate = pre_data['rate'].mean()
        volatility = pre_data['rate'].std()
        
        # Trend direction (linear regression slope)
        if len(pre_data) > 1:
            x = np.arange(len(pre_data))
            y = pre_data['rate'].values
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.01:
                trend_direction = 'up'
            elif slope < -0.01:
                trend_direction = 'down'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'stable'
            slope = 0
        
        # Change percent
        first_rate = pre_data.iloc[0]['rate']
        last_rate = pre_data.iloc[-1]['rate']
        change_percent = ((last_rate - first_rate) / first_rate) * 100 if first_rate != 0 else 0
        
        return {
            'avg_rate': avg_rate,
            'trend_direction': trend_direction,
            'volatility': volatility,
            'change_percent': change_percent,
            'slope': slope
        }
    
    def calculate_post_impact(self, grant_date, window_weeks=4):
        """
        Calculate currency impact after grant disbursement
        
        Args:
            grant_date: Date of grant
            window_weeks: Number of weeks to look forward
        
        Returns:
            dict: Post-period metrics
        """
        end_date = grant_date + timedelta(weeks=window_weeks)
        
        # Filter for post-period
        mask = (self.fx_data['date'] > grant_date) & (self.fx_data['date'] <= end_date)
        post_data = self.fx_data[mask].copy()
        
        if len(post_data) < 2:
            return {
                'avg_rate': 0,
                'trend_direction': 'unknown',
                'volatility': 0,
                'change_percent': 0
            }
        
        # Calculate metrics
        avg_rate = post_data['rate'].mean()
        volatility = post_data['rate'].std()
        
        # Trend
        if len(post_data) > 1:
            x = np.arange(len(post_data))
            y = post_data['rate'].values
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.01:
                trend_direction = 'up'
            elif slope < -0.01:
                trend_direction = 'down'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'stable'
            slope = 0
        
        # Change percent
        first_rate = post_data.iloc[0]['rate']
        last_rate = post_data.iloc[-1]['rate']
        change_percent = ((last_rate - first_rate) / first_rate) * 100 if first_rate != 0 else 0
        
        return {
            'avg_rate': avg_rate,
            'trend_direction': trend_direction,
            'volatility': volatility,
            'change_percent': change_percent,
            'slope': slope
        }
    
    def assess_commodity_influence(self, grant_date, window_weeks=4):
        """
        Assess commodity price stability during the period
        
        Args:
            grant_date: Date of grant
            window_weeks: Window size in weeks
        
        Returns:
            dict: Commodity influence metrics
        """
        start_date = grant_date - timedelta(weeks=window_weeks)
        end_date = grant_date + timedelta(weeks=window_weeks)
        
        commodity_volatilities = {}
        
        for commodity_name, commodity_df in self.commodity_data.items():
            # Ensure date column is datetime
            commodity_df['date'] = pd.to_datetime(commodity_df['date'])
            
            # Filter for period
            mask = (commodity_df['date'] >= start_date) & (commodity_df['date'] <= end_date)
            period_data = commodity_df[mask]
            
            if len(period_data) > 1:
                volatility = period_data['price'].std() / period_data['price'].mean() * 100  # CV%
                commodity_volatilities[commodity_name] = volatility
        
        if commodity_volatilities:
            avg_volatility = np.mean(list(commodity_volatilities.values()))
            
            # Classify stability
            if avg_volatility < 10:
                stability = 'high'
            elif avg_volatility < 20:
                stability = 'medium'
            else:
                stability = 'low'
        else:
            avg_volatility = 0
            stability = 'unknown'
        
        return {
            'avg_volatility': avg_volatility,
            'stability': stability,
            'individual_volatilities': commodity_volatilities
        }
    
    def determine_trend_break(self, pre_metrics, post_metrics):
        """
        Determine if grant caused a trend break or continuation
        
        Args:
            pre_metrics: Pre-grant metrics
            post_metrics: Post-grant metrics
        
        Returns:
            str: 'break' or 'continuation'
        """
        pre_direction = pre_metrics['trend_direction']
        post_direction = post_metrics['trend_direction']
        
        if pre_direction == post_direction:
            return 'continuation'
        elif pre_direction == 'stable' or post_direction == 'stable':
            return 'neutral'
        else:
            return 'break'
    
    def calculate_impact_score(self, pre_metrics, post_metrics, commodity_metrics):
        """
        Calculate overall impact score (1-5 scale)
        
        Scoring logic:
        - High commodity stability + significant deviation = High score
        - High commodity volatility + small deviation = Low score
        
        Args:
            pre_metrics: Pre-grant metrics
            post_metrics: Post-grant metrics
            commodity_metrics: Commodity influence metrics
        
        Returns:
            float: Impact score (1.0 to 5.0)
        """
        # Component 1: Commodity Stability Score (0-1)
        stability_map = {'high': 1.0, 'medium': 0.5, 'low': 0.2, 'unknown': 0.5}
        commodity_score = stability_map[commodity_metrics['stability']]
        
        # Component 2: Trend Deviation Score (0-1)
        # Higher score if trend changed significantly
        pre_slope = pre_metrics.get('slope', 0)
        post_slope = post_metrics.get('slope', 0)
        slope_change = abs(post_slope - pre_slope)
        deviation_score = min(slope_change * 10, 1.0)  # Normalize
        
        # Component 3: Magnitude Score (0-1)
        magnitude = abs(post_metrics['change_percent'])
        magnitude_score = min(magnitude / 20, 1.0)  # 20% = max score
        
        # Weighted combination
        weights = IMPACT_SCORE_WEIGHTS
        final_score = (
            weights['commodity_stability'] * commodity_score +
            weights['trend_deviation'] * deviation_score +
            weights['magnitude'] * magnitude_score
        )
        
        # Scale to 1-5
        impact_score = 1 + (final_score * 4)
        
        return round(impact_score, 2)
    
    def analyze_grant(self, grant_row, pre_weeks=4, post_weeks=4):
        """
        Perform full analysis for a single grant
        
        Args:
            grant_row: Single row from grants DataFrame
            pre_weeks: Pre-grant window
            post_weeks: Post-grant window
        
        Returns:
            dict: Complete analysis results
        """
        grant_date = grant_row['disbursement_date']
        
        # Calculate metrics
        pre_metrics = self.calculate_pre_trend(grant_date, pre_weeks)
        post_metrics = self.calculate_post_impact(grant_date, post_weeks)
        commodity_metrics = self.assess_commodity_influence(grant_date, (pre_weeks + post_weeks) // 2)
        
        # Determine trend break
        trend_status = self.determine_trend_break(pre_metrics, post_metrics)
        
        # Calculate impact score
        impact_score = self.calculate_impact_score(pre_metrics, post_metrics, commodity_metrics)
        
        return {
            'grant_date': grant_date,
            'grant_amount': grant_row['amount_usd'],
            'grant_source': grant_row['source'],
            'program_name': grant_row['program_name'],
            'pre_metrics': pre_metrics,
            'post_metrics': post_metrics,
            'commodity_metrics': commodity_metrics,
            'trend_status': trend_status,
            'impact_score': impact_score
        }
    
    def analyze_all_grants(self, pre_weeks=4, post_weeks=4):
        """
        Analyze all grants in the dataset
        
        Args:
            pre_weeks: Pre-grant window
            post_weeks: Post-grant window
        
        Returns:
            list: List of analysis results
        """
        results = []
        
        for idx, grant_row in self.grants_data.iterrows():
            analysis = self.analyze_grant(grant_row, pre_weeks, post_weeks)
            results.append(analysis)
        
        return results


if __name__ == '__main__':
    # Example usage placeholder
    print("Grant Impact Analyzer initialized")
