#!/usr/bin/env python3
"""
Automated Phase 3 Handler Migration Script

This script automates the migration of remaining handlers to use the Phase 3 
smart message system and batch operations.
"""

import os
import re
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class Phase3Migrator:
    """Automated Phase 3 handler migration utility"""
    
    def __init__(self, handlers_dir: str):
        self.handlers_dir = Path(handlers_dir)
        self.migration_patterns = self._init_migration_patterns()
        
    def _init_migration_patterns(self) -> List[Dict]:
        """Initialize migration patterns for common HandlerResponse scenarios"""
        return [
            # Import pattern
            {
                'name': 'Add Phase 3 imports',
                'pattern': r'from handlers\.base_handler import (.+?)HandlerRequest, HandlerResponse',
                'replacement': r'from handlers.base_handler import \1HandlerRequest, HandlerResponse, InteractionType, ContentType',
                'condition': lambda content: 'InteractionType, ContentType' not in content
            },
            
            # Menu navigation responses
            {
                'name': 'Menu navigation responses',
                'pattern': r'HandlerResponse\(\s*message=([^,]+),\s*keyboard=([^,]+),\s*next_state=([^,\)]+),\s*edit_message=True\s*\)',
                'replacement': r'self.create_smart_response(\n                message=\1,\n                keyboard=\2,\n                interaction_type=InteractionType.MENU_NAVIGATION,\n                content_type=ContentType.SELECTION,\n                next_state=\3\n            )'
            },
            
            # Form input responses
            {
                'name': 'Form input responses', 
                'pattern': r'HandlerResponse\(\s*message=([^,]+),\s*next_state=([^,\)]+),\s*edit_message=True\s*\)',
                'replacement': r'self.create_smart_response(\n                message=\1,\n                keyboard=None,\n                interaction_type=InteractionType.FORM_INPUT,\n                content_type=ContentType.INFO,\n                next_state=\2\n            )'
            },
            
            # Cancellation responses  
            {
                'name': 'Cancellation responses',
                'pattern': r'HandlerResponse\(\s*message=("[^"]*cancelad[oa][^"]*"),\s*end_conversation=True[^)]*\)',
                'replacement': r'self.create_smart_response(\n                message=\1,\n                keyboard=None,\n                interaction_type=InteractionType.CONFIRMATION,\n                content_type=ContentType.INFO,\n                end_conversation=True\n            )'
            },
            
            # Error responses
            {
                'name': 'Error responses',
                'pattern': r'HandlerResponse\(\s*message=("❌[^"]*"),\s*([^)]*)\)',
                'replacement': r'self.create_smart_response(\n                message=\1,\n                keyboard=None,\n                interaction_type=InteractionType.ERROR_DISPLAY,\n                content_type=ContentType.ERROR,\n                \2\n            )'
            },
            
            # Batch cleanup patterns
            {
                'name': 'Safe delete message calls',
                'pattern': r'await self\.safe_delete_message\(([^)]+)\)',
                'replacement': r'await self.batch_cleanup_messages([\1], strategy="instant")'
            },
        ]
    
    def get_handler_files(self) -> List[Path]:
        """Get all handler files that need migration"""
        handler_files = list(self.handlers_dir.glob('*_handler.py'))
        
        # Filter out already migrated handlers
        migrated = {'base_handler.py', 'relatorios_handler.py'}  # Known migrated
        
        # Check for InteractionType import to identify migrated files
        to_migrate = []
        for handler_file in handler_files:
            if handler_file.name in migrated:
                continue
                
            try:
                content = handler_file.read_text(encoding='utf-8')
                if 'InteractionType, ContentType' not in content:
                    to_migrate.append(handler_file)
                else:
                    logger.info(f"Already migrated: {handler_file.name}")
            except Exception as e:
                logger.warning(f"Could not read {handler_file.name}: {e}")
                
        return to_migrate
    
    def analyze_handler(self, handler_file: Path) -> Dict:
        """Analyze a handler file for migration opportunities"""
        try:
            content = handler_file.read_text(encoding='utf-8')
            
            analysis = {
                'file': handler_file.name,
                'handler_responses': len(re.findall(r'HandlerResponse\(', content)),
                'safe_delete_calls': len(re.findall(r'\.safe_delete_message\(', content)),
                'edit_message_usage': len(re.findall(r'edit_message\s*=\s*True', content)),
                'migration_potential': 0
            }
            
            # Calculate migration potential score
            analysis['migration_potential'] = (
                analysis['handler_responses'] * 2 + 
                analysis['safe_delete_calls'] * 3 +
                analysis['edit_message_usage'] * 1
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {handler_file.name}: {e}")
            return {'file': handler_file.name, 'error': str(e)}
    
    def migrate_handler(self, handler_file: Path, dry_run: bool = False) -> Dict:
        """Migrate a single handler file"""
        try:
            original_content = handler_file.read_text(encoding='utf-8')
            modified_content = original_content
            changes_made = []
            
            # Apply migration patterns
            for pattern_config in self.migration_patterns:
                pattern_name = pattern_config['name']
                pattern = pattern_config['pattern']
                replacement = pattern_config['replacement']
                
                # Check condition if specified
                if 'condition' in pattern_config:
                    if not pattern_config['condition'](modified_content):
                        continue
                
                # Apply pattern
                new_content, count = re.subn(pattern, replacement, modified_content, flags=re.MULTILINE | re.DOTALL)
                
                if count > 0:
                    changes_made.append(f"{pattern_name}: {count} replacements")
                    modified_content = new_content
            
            # Write changes if not dry run
            if not dry_run and changes_made:
                # Backup original file
                backup_file = handler_file.with_suffix('.py.backup')
                backup_file.write_text(original_content, encoding='utf-8')
                
                # Write migrated content
                handler_file.write_text(modified_content, encoding='utf-8')
                logger.info(f"Migrated {handler_file.name}")
                logger.info(f"Backup created: {backup_file.name}")
            
            return {
                'file': handler_file.name,
                'changes': changes_made,
                'success': True,
                'dry_run': dry_run
            }
            
        except Exception as e:
            logger.error(f"Error migrating {handler_file.name}: {e}")
            return {
                'file': handler_file.name,
                'error': str(e),
                'success': False
            }
    
    def migrate_all_handlers(self, dry_run: bool = False) -> Dict:
        """Migrate all handlers that need Phase 3 migration"""
        handler_files = self.get_handler_files()
        
        if not handler_files:
            logger.info("All handlers already migrated!")
            return {'total': 0, 'migrated': 0, 'errors': 0}
        
        logger.info(f"Found {len(handler_files)} handlers to migrate")
        
        results = {'total': len(handler_files), 'migrated': 0, 'errors': 0, 'details': []}
        
        # Analyze all handlers first
        logger.info("\nAnalysis Report:")
        logger.info("-" * 50)
        for handler_file in handler_files:
            analysis = self.analyze_handler(handler_file)
            if 'error' not in analysis:
                logger.info(f"{analysis['file']:25} | Score: {analysis['migration_potential']:2} | "
                           f"Responses: {analysis['handler_responses']:2} | "
                           f"Safe deletes: {analysis['safe_delete_calls']:2}")
        
        logger.info("-" * 50)
        
        if dry_run:
            logger.info("DRY RUN - No files will be modified")
        else:
            logger.info("LIVE RUN - Files will be modified")
        
        logger.info("\nMigration Progress:")
        logger.info("-" * 50)
        
        # Migrate handlers
        for handler_file in handler_files:
            result = self.migrate_handler(handler_file, dry_run)
            results['details'].append(result)
            
            if result['success']:
                if result['changes']:
                    results['migrated'] += 1
                    logger.info(f"MIGRATED: {result['file']}")
                    for change in result['changes']:
                        logger.info(f"   - {change}")
                else:
                    logger.info(f"SKIPPED: {result['file']} (no changes needed)")
            else:
                results['errors'] += 1
                logger.error(f"ERROR: {result['file']}: {result.get('error', 'Unknown error')}")
        
        return results
    
    def create_migration_report(self, results: Dict) -> str:
        """Create a detailed migration report"""
        report = f"""
# Phase 3 Handler Migration Report

## Summary
- **Total handlers processed:** {results['total']}
- **Successfully migrated:** {results['migrated']}
- **Errors encountered:** {results['errors']}
- **Success rate:** {(results['migrated'] / results['total'] * 100) if results['total'] > 0 else 0:.1f}%

## Detailed Results
"""
        
        for detail in results.get('details', []):
            report += f"\n### {detail['file']}\n"
            if detail['success']:
                if detail.get('changes'):
                    report += "**Status:** ✅ Migrated\n"
                    report += "**Changes made:**\n"
                    for change in detail['changes']:
                        report += f"- {change}\n"
                else:
                    report += "**Status:** ⏩ No changes needed\n"
            else:
                report += f"**Status:** ❌ Error - {detail.get('error', 'Unknown')}\n"
        
        report += f"\n## Next Steps\n"
        report += "1. Test all migrated handlers\n"
        report += "2. Run compliance validation\n" 
        report += "3. Update documentation\n"
        report += "4. Deploy to production\n"
        
        return report


def main():
    """Main migration execution"""
    print("Phase 3 Handler Migration Utility")
    print("=" * 50)
    
    # Get handlers directory
    handlers_dir = Path(__file__).parent / 'handlers'
    if not handlers_dir.exists():
        logger.error(f"Handlers directory not found: {handlers_dir}")
        return 1
    
    migrator = Phase3Migrator(str(handlers_dir))
    
    # Parse arguments
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    create_report = '--report' in sys.argv or '-r' in sys.argv
    
    # Run migration
    results = migrator.migrate_all_handlers(dry_run=dry_run)
    
    # Create report if requested
    if create_report:
        report_content = migrator.create_migration_report(results)
        report_file = Path('PHASE3_MIGRATION_REPORT.md')
        report_file.write_text(report_content, encoding='utf-8')
        logger.info(f"📄 Report saved to: {report_file}")
    
    # Print summary
    print(f"\nMigration Complete!")
    print(f"   Migrated: {results['migrated']}/{results['total']} handlers")
    print(f"   Errors: {results['errors']}")
    
    if dry_run:
        print("\nThis was a dry run. Use without --dry-run to apply changes.")
    
    return 0 if results['errors'] == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)