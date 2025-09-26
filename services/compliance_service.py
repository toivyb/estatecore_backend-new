"""
Main Compliance Service
Central orchestrator for the Automated Compliance Monitoring system
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import schedule
import time
from threading import Thread

from models.base import db
from models.compliance import ComplianceMetrics, ComplianceViolation
from services.regulatory_knowledge_service import get_regulatory_knowledge_service
from services.compliance_integration_service import get_compliance_integration_service
from services.violation_detection_service import get_violation_detection_service
from services.compliance_alert_service import get_compliance_alert_service, AlertType
from services.compliance_reporting_service import get_compliance_reporting_service, ReportType, ReportFormat
from ai_modules.compliance.ai_compliance_monitor import get_ai_compliance_monitor


logger = logging.getLogger(__name__)


@dataclass
class ComplianceSystemStatus:
    """Overall status of the compliance system"""
    is_healthy: bool
    services_status: Dict[str, str]
    last_check: datetime
    active_monitors: int
    pending_alerts: int
    system_uptime: float


class ComplianceOrchestrator:
    """Main orchestrator for compliance system operations"""
    
    def __init__(self):
        self.regulatory_service = get_regulatory_knowledge_service()
        self.integration_service = get_compliance_integration_service()
        self.detection_service = get_violation_detection_service()
        self.alert_service = get_compliance_alert_service()
        self.reporting_service = get_compliance_reporting_service()
        self.ai_monitor = get_ai_compliance_monitor()
        
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.is_running = False
        self.scheduler_thread = None
        self.start_time = datetime.now()
        
    def start_system(self) -> bool:
        """Start the compliance monitoring system"""
        try:
            logger.info("Starting Compliance Monitoring System...")
            
            # Initialize regulatory knowledge base
            if not self.regulatory_service.initialize_knowledge_base():
                logger.error("Failed to initialize regulatory knowledge base")
                return False
            
            # Initialize integrations
            asyncio.run(self.integration_service.initialize_integrations())
            
            # Start scheduled tasks
            self._setup_scheduled_tasks()
            self._start_scheduler()
            
            self.is_running = True
            logger.info("Compliance Monitoring System started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start compliance system: {e}")
            return False
    
    def stop_system(self):
        """Stop the compliance monitoring system"""
        try:
            logger.info("Stopping Compliance Monitoring System...")
            
            self.is_running = False
            
            # Stop scheduler
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            logger.info("Compliance Monitoring System stopped")
            
        except Exception as e:
            logger.error(f"Error stopping compliance system: {e}")
    
    def _setup_scheduled_tasks(self):
        """Setup scheduled tasks for compliance monitoring"""
        try:
            # Continuous monitoring every 5 minutes
            schedule.every(5).minutes.do(self._run_continuous_monitoring)
            
            # Violation detection every 15 minutes
            schedule.every(15).minutes.do(self._run_violation_detection)
            
            # Integration sync every hour
            schedule.every().hour.do(self._sync_integrations)
            
            # AI model training daily at 2 AM
            schedule.every().day.at("02:00").do(self._train_ai_models)
            
            # Generate daily reports at 6 AM
            schedule.every().day.at("06:00").do(self._generate_daily_reports)
            
            # Weekly compliance review on Mondays at 9 AM
            schedule.every().monday.at("09:00").do(self._weekly_compliance_review)
            
            # Regulatory updates check twice daily
            schedule.every(12).hours.do(self._check_regulatory_updates)
            
            logger.info("Scheduled tasks configured successfully")
            
        except Exception as e:
            logger.error(f"Error setting up scheduled tasks: {e}")
    
    def _start_scheduler(self):
        """Start the task scheduler in a separate thread"""
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Task scheduler started")
    
    def _run_continuous_monitoring(self):
        """Run continuous compliance monitoring"""
        try:
            logger.debug("Running continuous monitoring...")
            
            # This would monitor for real-time events and trigger immediate responses
            # For now, we'll run a light monitoring cycle
            
            # Check for critical violations that need immediate attention
            critical_violations = db.session.query(ComplianceViolation).filter_by(
                severity=ViolationSeverity.CRITICAL,
                is_resolved=False
            ).filter(
                ComplianceViolation.detected_date >= datetime.now() - timedelta(hours=1)
            ).all()
            
            # Create alerts for new critical violations
            for violation in critical_violations:
                asyncio.run(self.alert_service.create_alert(
                    alert_type=AlertType.VIOLATION_DETECTED,
                    title=f"Critical Violation: {violation.title}",
                    message=f"Critical compliance violation detected at property {violation.property_id}",
                    priority=violation.severity,
                    property_id=violation.property_id,
                    violation_id=violation.id,
                    recipient_roles=['property_manager', 'compliance_manager'],
                    template_data={
                        'violation_type': violation.violation_type,
                        'severity': violation.severity.value,
                        'description': violation.description,
                        'detected_date': violation.detected_date.isoformat(),
                        'property_id': violation.property_id
                    }
                ))
            
            logger.debug(f"Continuous monitoring completed - {len(critical_violations)} critical violations processed")
            
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")
    
    def _run_violation_detection(self):
        """Run comprehensive violation detection"""
        try:
            logger.info("Running violation detection...")
            
            # Run detection asynchronously
            results = asyncio.run(self.detection_service.run_comprehensive_violation_detection())
            
            violations_detected = len(results.get('violations_detected', []))
            high_risk_properties = len(results.get('high_risk_properties', []))
            
            logger.info(f"Violation detection completed - {violations_detected} violations detected, {high_risk_properties} high-risk properties")
            
            # Create alerts for high-risk properties
            for property_info in results.get('high_risk_properties', []):
                if property_info['risk_level'] == 'critical':
                    asyncio.run(self.alert_service.create_alert(
                        alert_type=AlertType.HIGH_RISK_PROPERTY,
                        title=f"High Risk Property Alert: {property_info['property_id']}",
                        message=f"Property flagged as high risk with score {property_info['risk_score']:.1f}",
                        priority=ViolationSeverity.HIGH,
                        property_id=property_info['property_id'],
                        recipient_roles=['property_manager', 'regional_manager'],
                        template_data={
                            'property_id': property_info['property_id'],
                            'risk_score': property_info['risk_score'],
                            'risk_level': property_info['risk_level'],
                            'risk_factors': ', '.join(property_info['high_risk_factors'])
                        }
                    ))
            
        except Exception as e:
            logger.error(f"Error running violation detection: {e}")
    
    def _sync_integrations(self):
        """Sync data from all integrations"""
        try:
            logger.info("Syncing integrations...")
            
            results = asyncio.run(self.integration_service.sync_all_integrations())
            total_synced = sum(results.values())
            
            logger.info(f"Integration sync completed - {total_synced} data points synced")
            
        except Exception as e:
            logger.error(f"Error syncing integrations: {e}")
    
    def _train_ai_models(self):
        """Train AI models with new data"""
        try:
            logger.info("Training AI models...")
            
            # Train models with new compliance data
            success = self.ai_monitor.train_models_with_new_data()
            
            if success:
                logger.info("AI models trained successfully")
            else:
                logger.warning("AI model training completed with some issues")
                
        except Exception as e:
            logger.error(f"Error training AI models: {e}")
    
    def _generate_daily_reports(self):
        """Generate daily compliance reports"""
        try:
            logger.info("Generating daily reports...")
            
            # Generate executive dashboard report
            report_result = asyncio.run(self.reporting_service.generate_standard_report(
                report_type=ReportType.EXECUTIVE_DASHBOARD,
                format=ReportFormat.PDF
            ))
            
            if report_result.get('success'):
                logger.info("Daily executive report generated successfully")
                
                # Here you would typically:
                # 1. Save the report to a file storage system
                # 2. Send the report to stakeholders via email
                # 3. Update the report archive
                
            else:
                logger.error(f"Failed to generate daily report: {report_result.get('error')}")
            
        except Exception as e:
            logger.error(f"Error generating daily reports: {e}")
    
    def _weekly_compliance_review(self):
        """Perform weekly compliance review and analysis"""
        try:
            logger.info("Performing weekly compliance review...")
            
            # Generate comprehensive weekly report
            report_result = asyncio.run(self.reporting_service.generate_standard_report(
                report_type=ReportType.VIOLATION_ANALYSIS,
                format=ReportFormat.PDF
            ))
            
            # Check for overdue compliance requirements
            overdue_requirements = db.session.query(ComplianceRequirement).filter(
                ComplianceRequirement.next_review_date < datetime.now(),
                ComplianceRequirement.compliance_status != ComplianceStatus.COMPLIANT
            ).all()
            
            # Create alerts for overdue requirements
            for requirement in overdue_requirements[:10]:  # Limit to prevent spam
                asyncio.run(self.alert_service.create_alert(
                    alert_type=AlertType.OVERDUE_REQUIREMENT,
                    title=f"Overdue Compliance Requirement: {requirement.requirement_name}",
                    message=f"Compliance requirement is overdue for review",
                    priority=ViolationSeverity.HIGH,
                    property_id=requirement.property_id,
                    requirement_id=requirement.id,
                    recipient_roles=['property_manager', 'compliance_manager'],
                    template_data={
                        'requirement_name': requirement.requirement_name,
                        'due_date': requirement.next_review_date.isoformat(),
                        'property_id': requirement.property_id,
                        'days_overdue': (datetime.now() - requirement.next_review_date).days
                    }
                ))
            
            logger.info(f"Weekly compliance review completed - {len(overdue_requirements)} overdue requirements processed")
            
        except Exception as e:
            logger.error(f"Error in weekly compliance review: {e}")
    
    def _check_regulatory_updates(self):
        """Check for regulatory updates"""
        try:
            logger.info("Checking for regulatory updates...")
            
            updates = self.regulatory_service.check_regulation_updates()
            
            if updates:
                logger.info(f"Found {len(updates)} regulatory updates")
                
                # Create alerts for significant updates
                for update in updates:
                    if update.impact_level in ['high', 'critical']:
                        asyncio.run(self.alert_service.create_alert(
                            alert_type=AlertType.REGULATORY_CHANGES,
                            title=f"Regulatory Update: {update.regulation_code}",
                            message=f"Important regulatory change detected requiring attention",
                            priority=ViolationSeverity.HIGH if update.impact_level == 'high' else ViolationSeverity.CRITICAL,
                            recipient_roles=['compliance_manager', 'legal_team'],
                            template_data={
                                'regulation_code': update.regulation_code,
                                'title': update.title,
                                'changes': update.changes,
                                'effective_date': update.effective_date.isoformat(),
                                'impact_level': update.impact_level
                            }
                        ))
            else:
                logger.debug("No regulatory updates found")
                
        except Exception as e:
            logger.error(f"Error checking regulatory updates: {e}")
    
    async def get_system_status(self) -> ComplianceSystemStatus:
        """Get current system status"""
        try:
            services_status = {}
            
            # Check each service
            try:
                self.regulatory_service.get_regulation_statistics()
                services_status['regulatory_service'] = 'healthy'
            except Exception:
                services_status['regulatory_service'] = 'error'
            
            try:
                integration_status = await self.integration_service.get_integration_status()
                services_status['integration_service'] = 'healthy' if integration_status else 'warning'
            except Exception:
                services_status['integration_service'] = 'error'
            
            services_status['detection_service'] = 'healthy'  # Always healthy if system is running
            services_status['alert_service'] = 'healthy'
            services_status['reporting_service'] = 'healthy'
            services_status['ai_monitor'] = 'healthy'
            
            # Count active monitors and pending alerts
            active_monitors = len([s for s in services_status.values() if s == 'healthy'])
            
            pending_alerts = db.session.query(ComplianceAlert).filter_by(
                acknowledged=False
            ).count()
            
            # Calculate uptime
            uptime = (datetime.now() - self.start_time).total_seconds() / 3600  # Hours
            
            # Overall health
            is_healthy = all(status != 'error' for status in services_status.values())
            
            return ComplianceSystemStatus(
                is_healthy=is_healthy,
                services_status=services_status,
                last_check=datetime.now(),
                active_monitors=active_monitors,
                pending_alerts=pending_alerts,
                system_uptime=uptime
            )
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return ComplianceSystemStatus(
                is_healthy=False,
                services_status={},
                last_check=datetime.now(),
                active_monitors=0,
                pending_alerts=0,
                system_uptime=0
            )
    
    async def run_manual_compliance_check(self, property_ids: List[str] = None) -> Dict[str, Any]:
        """Run manual compliance check for specific properties"""
        try:
            logger.info(f"Running manual compliance check for {len(property_ids) if property_ids else 'all'} properties")
            
            # Run violation detection
            detection_results = await self.detection_service.run_comprehensive_violation_detection(property_ids)
            
            # Run AI analysis for each property
            ai_results = {}
            if property_ids:
                for property_id in property_ids:
                    ai_results[property_id] = self.ai_monitor.analyze_property_compliance(property_id)
            
            # Generate summary
            summary = {
                'properties_analyzed': detection_results.get('properties_analyzed', 0),
                'violations_detected': len(detection_results.get('violations_detected', [])),
                'high_risk_properties': len(detection_results.get('high_risk_properties', [])),
                'recommendations_generated': len(detection_results.get('prevention_recommendations', [])),
                'ai_analysis_results': ai_results,
                'patterns_identified': detection_results.get('patterns_identified', []),
                'completed_at': datetime.now()
            }
            
            logger.info("Manual compliance check completed successfully")
            return {
                'success': True,
                'summary': summary,
                'detailed_results': detection_results
            }
            
        except Exception as e:
            logger.error(f"Error in manual compliance check: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global orchestrator instance
_compliance_orchestrator = None


def get_compliance_orchestrator() -> ComplianceOrchestrator:
    """Get or create the compliance orchestrator instance"""
    global _compliance_orchestrator
    if _compliance_orchestrator is None:
        _compliance_orchestrator = ComplianceOrchestrator()
    return _compliance_orchestrator


def start_compliance_system():
    """Start the compliance monitoring system"""
    orchestrator = get_compliance_orchestrator()
    return orchestrator.start_system()


def stop_compliance_system():
    """Stop the compliance monitoring system"""
    orchestrator = get_compliance_orchestrator()
    orchestrator.stop_system()


# CLI Commands
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start":
            if start_compliance_system():
                print("Compliance system started successfully")
                try:
                    while True:
                        time.sleep(60)  # Keep running
                except KeyboardInterrupt:
                    print("\nStopping compliance system...")
                    stop_compliance_system()
            else:
                print("Failed to start compliance system")
                sys.exit(1)
                
        elif command == "stop":
            stop_compliance_system()
            print("Compliance system stopped")
            
        elif command == "status":
            orchestrator = get_compliance_orchestrator()
            status = asyncio.run(orchestrator.get_system_status())
            print(f"System Health: {'Healthy' if status.is_healthy else 'Unhealthy'}")
            print(f"Active Monitors: {status.active_monitors}")
            print(f"Pending Alerts: {status.pending_alerts}")
            print(f"Uptime: {status.system_uptime:.2f} hours")
            
        elif command == "check":
            # Run manual compliance check
            orchestrator = get_compliance_orchestrator()
            results = asyncio.run(orchestrator.run_manual_compliance_check())
            if results['success']:
                print("Manual compliance check completed")
                print(f"Properties analyzed: {results['summary']['properties_analyzed']}")
                print(f"Violations detected: {results['summary']['violations_detected']}")
            else:
                print(f"Manual compliance check failed: {results['error']}")
                
        else:
            print("Usage: python compliance_service.py [start|stop|status|check]")
    else:
        print("Usage: python compliance_service.py [start|stop|status|check]")