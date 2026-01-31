import os
import sys
import logging
import hashlib
from datetime import datetime
from threading import Lock
from cnf_parser_ext import ConfigParserExt
from plane import Plane
from colorama import Fore, Style

class ConfigManager:
    """Manages plane configurations with conflict detection and hot-reloading"""
    
    def __init__(self, config_dir="./configs"):
        self.config_dir = os.path.abspath(config_dir)
        # Maps: file_path -> (icao, pia_icao_or_None)
        self.file_to_icaos = {}
        # Maps: icao/pia_icao -> file_path (for conflict detection)
        self.icao_to_file = {}
        # Lock for thread-safe operations
        self.lock = Lock()
        
        # Setup config change logger
        self.change_logger = self._setup_change_logger()
    
    def _setup_change_logger(self):
        """Setup dedicated logger for config changes"""
        logger = logging.getLogger('config_changes')
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers = []
        
        # Create logs directory if it doesn't exist
        os.makedirs('./logs', exist_ok=True)
        
        # File handler with detailed formatting
        file_handler = logging.FileHandler('./logs/config_changes.log')
        file_handler.setLevel(logging.INFO)
        
        # Format: timestamp | event_type | file | details
        formatter = logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.propagate = False  # Don't propagate to root logger
        
        return logger
        
    def get_relative_path(self, abs_path):
        """Convert absolute path to relative path from config directory"""
        rel_path = os.path.relpath(abs_path, self.config_dir)
        return rel_path
    
    def validate_no_conflict(self, icao, pia_icao, file_path):
        """Check if ICAO or PIA_ICAO conflicts with existing configs"""
        rel_path = self.get_relative_path(file_path)
        
        # Check ICAO conflict
        if icao in self.icao_to_file:
            existing_file = self.icao_to_file[icao]
            if existing_file != file_path:
                existing_rel = self.get_relative_path(existing_file)
                raise ValueError(f"ICAO conflict: {icao} in {rel_path} conflicts with {existing_rel}")
        
        # Check PIA_ICAO conflict
        if pia_icao and pia_icao in self.icao_to_file:
            existing_file = self.icao_to_file[pia_icao]
            if existing_file != file_path:
                existing_rel = self.get_relative_path(existing_file)
                raise ValueError(f"PIA_ICAO conflict: {pia_icao} in {rel_path} conflicts with {existing_rel}")
    
    def load_config_file(self, file_path):
        """Load and parse a single config file, return (config, icao, pia_icao_or_None)"""
        plane_config = ConfigParserExt()
        plane_config.read(file_path)
        
        icao = plane_config.get('DATA', 'ICAO').lower()
        pia_icao = None
        if plane_config.has_option('DATA', 'PIA_ICAO'):
            pia_icao = plane_config.get('DATA', 'PIA_ICAO').lower()
        
        return plane_config, icao, pia_icao
    
    def register_config(self, file_path, icao, pia_icao):
        """Register config file and its ICAOs in tracking dicts"""
        with self.lock:
            self.file_to_icaos[file_path] = (icao, pia_icao)
            self.icao_to_file[icao] = file_path
            if pia_icao:
                self.icao_to_file[pia_icao] = file_path
    
    def unregister_config(self, file_path):
        """Remove config file and its ICAOs from tracking dicts"""
        with self.lock:
            if file_path in self.file_to_icaos:
                icao, pia_icao = self.file_to_icaos[file_path]
                
                # Remove ICAO mapping
                if icao in self.icao_to_file and self.icao_to_file[icao] == file_path:
                    del self.icao_to_file[icao]
                
                # Remove PIA_ICAO mapping
                if pia_icao and pia_icao in self.icao_to_file and self.icao_to_file[pia_icao] == file_path:
                    del self.icao_to_file[pia_icao]
                
                del self.file_to_icaos[file_path]
                
                return icao, pia_icao
        return None, None
    
    def load_all_configs(self, planes_list):
        """Load all config files on startup and populate planes list"""
        print("Found the following configs")
        for dirpath, dirname, filenames in os.walk(self.config_dir):
            for filename in [f for f in filenames if f.endswith(".ini") and f != "mainconf.ini"]:
                if "disabled" not in dirpath:
                    file_path = os.path.join(dirpath, filename)
                    print(file_path)
                    
                    try:
                        plane_config, icao, pia_icao = self.load_config_file(file_path)
                        
                        # Validate no conflicts
                        self.validate_no_conflict(icao, pia_icao, file_path)
                        
                        # Create plane object
                        plane = Plane(icao, plane_config)
                        
                        # Add to planes list (only one entry per unique plane)
                        planes_list.append(plane)
                        
                        # Register in tracking
                        self.register_config(file_path, icao, pia_icao)
                        
                    except Exception as e:
                        print(f"{Fore.RED}Error loading {self.get_relative_path(file_path)}: {e}{Style.RESET_ALL}")
                        raise
        
        print(f"{len(planes_list)} planes configured.")
        return len(planes_list)
    
    def reload_all_configs(self, planes_list):
        """Reload all config files and update planes list"""
        import hashlib
        
        print(f"\n{Fore.CYAN}=== Reloading all configs ==={Style.RESET_ALL}")
        
        # Get current files and their hashes
        current_files = set()
        new_planes = []
        reloaded_count = 0
        modified_count = 0
        added_count = 0
        removed_count = 0
        
        # Scan for all config files
        for dirpath, dirname, filenames in os.walk(self.config_dir):
            for filename in [f for f in filenames if f.endswith(".ini") and f != "mainconf.ini"]:
                if "disabled" not in dirpath:
                    file_path = os.path.join(dirpath, filename)
                    current_files.add(file_path)
                    
                    try:
                        plane_config, icao, pia_icao = self.load_config_file(file_path)
                        
                        # Calculate file hash to detect actual changes
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        
                        # Check if this is a modification or addition
                        if file_path in self.file_to_icaos:
                            # Existing file - find the plane object from current list
                            old_icao, old_pia_icao = self.file_to_icaos[file_path]
                            plane = None
                            for p in planes_list:
                                if p.icao == old_icao:
                                    plane = p
                                    break
                            
                            if plane:
                                # Check if config actually changed
                                old_hash = getattr(plane, '_config_hash', None)
                                if old_hash != file_hash:
                                    modified_count += 1
                                    rel_path = self.get_relative_path(file_path)
                                    print(f"{Fore.YELLOW}Modified: {rel_path}{Style.RESET_ALL}")
                                
                                # Update existing plane
                                plane.config = plane_config
                                plane.icao = icao
                                plane.pia_icao = pia_icao
                                plane._config_hash = file_hash
                                
                                new_planes.append(plane)
                                reloaded_count += 1
                            else:
                                # Plane lost, create new
                                plane = Plane(icao, plane_config)
                                plane._config_hash = file_hash
                                new_planes.append(plane)
                                added_count += 1
                        else:
                            # New file
                            plane = Plane(icao, plane_config)
                            plane._config_hash = file_hash
                            new_planes.append(plane)
                            added_count += 1
                            rel_path = self.get_relative_path(file_path)
                            print(f"{Fore.GREEN}Added: {rel_path}{Style.RESET_ALL}")
                        
                        # Update tracking
                        self.file_to_icaos[file_path] = (icao, pia_icao)
                        self.icao_to_file[icao] = file_path
                        if pia_icao:
                            self.icao_to_file[pia_icao] = file_path
                        
                    except Exception as e:
                        rel_path = self.get_relative_path(file_path)
                        print(f"{Fore.RED}Error reloading {rel_path}: {e}{Style.RESET_ALL}")
        
        # Find removed files
        removed_files = set(self.file_to_icaos.keys()) - current_files
        for file_path in removed_files:
            removed_count += 1
            icao, pia_icao = self.file_to_icaos.get(file_path, (None, None))
            if icao:
                rel_path = self.get_relative_path(file_path)
                print(f"{Fore.RED}Removed: {rel_path} (ICAO: {icao}){Style.RESET_ALL}")
        
        # Clear and update planes list
        planes_list.clear()
        planes_list.extend(new_planes)
        
        # Clean up tracking for removed files
        for file_path in removed_files:
            self.unregister_config(file_path)
        
        unchanged_count = reloaded_count - modified_count
        
        print(f"{Fore.GREEN}Reload complete: {len(planes_list)} planes configured{Style.RESET_ALL}")
        print(f"  Modified: {modified_count}, Added: {added_count}, Removed: {removed_count}, Unchanged: {unchanged_count}")
        
        # Log the reload
        self.change_logger.info(f"RELOAD | Total: {len(planes_list)} | Modified: {modified_count} | Added: {added_count} | Removed: {removed_count} | Unchanged: {unchanged_count}")
        
        return {
            "total_planes": len(planes_list),
            "modified": modified_count,
            "added": added_count,
            "removed": removed_count,
            "unchanged": unchanged_count
        }


def verify_configs_only(config_dir="./configs"):
    """Verify all configs without creating plane objects - for standalone validation"""
    print(f"{Fore.CYAN}=== Config Verification Mode ==={Style.RESET_ALL}\n")
    
    config_manager = ConfigManager(config_dir)
    
    # Track stats
    total_files = 0
    total_planes = 0
    planes_with_pia = 0
    errors = []
    icao_list = []
    pia_list = []
    
    print("Scanning config files...\n")
    
    for dirpath, dirname, filenames in os.walk(config_manager.config_dir):
        for filename in [f for f in filenames if f.endswith(".ini") and f != "mainconf.ini"]:
            if "disabled" not in dirpath:
                file_path = os.path.join(dirpath, filename)
                rel_path = config_manager.get_relative_path(file_path)
                total_files += 1
                
                try:
                    # Load config
                    plane_config, icao, pia_icao = config_manager.load_config_file(file_path)
                    
                    # Validate no conflicts
                    config_manager.validate_no_conflict(icao, pia_icao, file_path)
                    
                    # Register it
                    config_manager.register_config(file_path, icao, pia_icao)
                    
                    # Track stats
                    total_planes += 1
                    icao_list.append(icao)
                    if pia_icao:
                        planes_with_pia += 1
                        pia_list.append(pia_icao)
                    
                    # Print success
                    if pia_icao:
                        print(f"{Fore.GREEN}✓{Style.RESET_ALL} {rel_path:<50} {icao:<8} (PIA: {pia_icao})")
                    else:
                        print(f"{Fore.GREEN}✓{Style.RESET_ALL} {rel_path:<50} {icao}")
                    
                except Exception as e:
                    errors.append((rel_path, str(e)))
                    print(f"{Fore.RED}✗{Style.RESET_ALL} {rel_path:<50} {Fore.RED}ERROR: {e}{Style.RESET_ALL}")
    
    # Print summary
    print(f"\n{Fore.CYAN}=== Verification Summary ==={Style.RESET_ALL}")
    print(f"Total config files scanned: {total_files}")
    print(f"Valid planes configured: {Fore.GREEN}{total_planes}{Style.RESET_ALL}")
    print(f"Planes with PIA_ICAO: {planes_with_pia}")
    print(f"Total ICAO keys: {total_planes}")
    print(f"Total PIA_ICAO keys: {planes_with_pia}")
    print(f"Total dictionary keys: {Fore.CYAN}{total_planes + planes_with_pia}{Style.RESET_ALL}")
    
    if errors:
        print(f"\n{Fore.RED}=== Errors Found ({len(errors)}) ==={Style.RESET_ALL}")
        for rel_path, error in errors:
            print(f"  {Fore.RED}✗{Style.RESET_ALL} {rel_path}")
            print(f"    {error}")
        return False
    else:
        print(f"\n{Fore.GREEN}✓ All configs valid - no conflicts detected{Style.RESET_ALL}")
        return True


if __name__ == "__main__":
    """Run standalone config verification"""
    success = verify_configs_only()
    sys.exit(0 if success else 1)
