"""
Cloud Regions Data Management

Provides comprehensive region information for cloud providers with
search, filtering, and popularity features for location dropdowns.
"""

from typing import Dict, List, Optional


class CloudRegionsData:
    """Manages cloud provider region information with search capabilities"""
    
    def __init__(self):
        self._regions_cache = {}
        self._load_region_definitions()
    
    def _load_region_definitions(self):
        """Load region definitions for all supported providers"""
        
        # Google Cloud Vertex AI Regions
        self._regions_cache["vertex_ai"] = [
            # Popular US regions (most commonly used)
            {"code": "us-central1", "name": "Iowa, USA", "popular": True},
            {"code": "us-east1", "name": "South Carolina, USA", "popular": True},
            {"code": "us-west1", "name": "Oregon, USA", "popular": True},
            {"code": "us-west2", "name": "California (Los Angeles), USA", "popular": True},
            
            # Popular European regions
            {"code": "europe-west1", "name": "Belgium", "popular": True},
            {"code": "europe-west2", "name": "London, UK", "popular": True},
            {"code": "europe-west3", "name": "Frankfurt, Germany", "popular": True},
            
            # Popular Asia-Pacific regions
            {"code": "asia-northeast1", "name": "Tokyo, Japan", "popular": True},
            {"code": "asia-southeast1", "name": "Singapore", "popular": True},
            
            # Additional US regions
            {"code": "us-east4", "name": "Northern Virginia, USA", "popular": False},
            {"code": "us-west3", "name": "Salt Lake City, USA", "popular": False},
            {"code": "us-west4", "name": "Las Vegas, USA", "popular": False},
            
            # Additional European regions
            {"code": "europe-central2", "name": "Warsaw, Poland", "popular": False},
            {"code": "europe-north1", "name": "Finland", "popular": False},
            {"code": "europe-west4", "name": "Netherlands", "popular": False},
            {"code": "europe-west6", "name": "Zurich, Switzerland", "popular": False},
            
            # Additional Asia-Pacific regions
            {"code": "asia-east1", "name": "Taiwan", "popular": False},
            {"code": "asia-east2", "name": "Hong Kong", "popular": False},
            {"code": "asia-northeast2", "name": "Osaka, Japan", "popular": False},
            {"code": "asia-northeast3", "name": "Seoul, South Korea", "popular": False},
            {"code": "asia-south1", "name": "Mumbai, India", "popular": False},
            {"code": "asia-southeast2", "name": "Jakarta, Indonesia", "popular": False},
            
            # Australia and other regions
            {"code": "australia-southeast1", "name": "Sydney, Australia", "popular": False},
            {"code": "australia-southeast2", "name": "Melbourne, Australia", "popular": False},
            {"code": "northamerica-northeast1", "name": "Montreal, Canada", "popular": False},
            {"code": "southamerica-east1", "name": "São Paulo, Brazil", "popular": False},
        ]
        
        # Azure OpenAI Regions
        self._regions_cache["azure_openai"] = [
            # Popular US regions
            {"code": "eastus", "name": "East US (Virginia)", "popular": True},
            {"code": "eastus2", "name": "East US 2 (Virginia)", "popular": True},
            {"code": "westus", "name": "West US (California)", "popular": True},
            {"code": "westus2", "name": "West US 2 (Washington)", "popular": True},
            {"code": "centralus", "name": "Central US (Iowa)", "popular": True},
            
            # Popular European regions
            {"code": "westeurope", "name": "West Europe (Netherlands)", "popular": True},
            {"code": "northeurope", "name": "North Europe (Ireland)", "popular": True},
            {"code": "uksouth", "name": "UK South (London)", "popular": True},
            
            # Popular Asia-Pacific regions
            {"code": "eastasia", "name": "East Asia (Hong Kong)", "popular": True},
            {"code": "southeastasia", "name": "Southeast Asia (Singapore)", "popular": True},
            {"code": "japaneast", "name": "Japan East (Tokyo)", "popular": True},
            
            # Additional US regions
            {"code": "northcentralus", "name": "North Central US (Illinois)", "popular": False},
            {"code": "southcentralus", "name": "South Central US (Texas)", "popular": False},
            {"code": "westcentralus", "name": "West Central US (Wyoming)", "popular": False},
            {"code": "westus3", "name": "West US 3 (Arizona)", "popular": False},
            
            # Additional European regions
            {"code": "francecentral", "name": "France Central (Paris)", "popular": False},
            {"code": "germanywestcentral", "name": "Germany West Central (Frankfurt)", "popular": False},
            {"code": "norwayeast", "name": "Norway East (Oslo)", "popular": False},
            {"code": "switzerlandnorth", "name": "Switzerland North (Zurich)", "popular": False},
            
            # Additional Asia-Pacific regions
            {"code": "japanwest", "name": "Japan West (Osaka)", "popular": False},
            {"code": "koreacentral", "name": "Korea Central (Seoul)", "popular": False},
            {"code": "koreasouth", "name": "Korea South (Busan)", "popular": False},
            {"code": "australiaeast", "name": "Australia East (Sydney)", "popular": False},
            {"code": "australiasoutheast", "name": "Australia Southeast (Melbourne)", "popular": False},
            {"code": "centralindia", "name": "Central India (Mumbai)", "popular": False},
            {"code": "southindia", "name": "South India (Chennai)", "popular": False},
        ]
        
        # Direct Vertex AI uses same regions as vertex_ai
        self._regions_cache["direct_vertex_ai"] = self._regions_cache["vertex_ai"]
    
    def get_regions(self, provider: str) -> List[Dict[str, any]]:
        """Get all regions for a provider"""
        return self._regions_cache.get(provider, []).copy()
    
    def get_popular_regions(self, provider: str) -> List[Dict[str, any]]:
        """Get only popular regions for a provider"""
        all_regions = self.get_regions(provider)
        return [region for region in all_regions if region.get("popular", False)]
    
    def search_regions(self, provider: str, query: str) -> List[Dict[str, any]]:
        """Search regions by code or name"""
        if not query:
            return self.get_regions(provider)
        
        query_lower = query.lower()
        all_regions = self.get_regions(provider)
        
        matching_regions = []
        for region in all_regions:
            code_match = query_lower in region["code"].lower()
            name_match = query_lower in region["name"].lower()
            
            if code_match or name_match:
                matching_regions.append(region)
        
        return matching_regions
    
    def validate_region(self, provider: str, region_code: str) -> bool:
        """Validate if a region code is known for this provider"""
        all_regions = self.get_regions(provider)
        known_codes = [region["code"] for region in all_regions]
        return region_code in known_codes
    
    def get_region_display_name(self, provider: str, region_code: str) -> str:
        """Get display name for a region code"""
        all_regions = self.get_regions(provider)
        
        for region in all_regions:
            if region["code"] == region_code:
                return f"{region['code']} ({region['name']})"
        
        # Return code as-is if not found (custom region)
        return region_code
    
    def get_supported_providers(self) -> List[str]:
        """Get list of supported cloud providers"""
        return list(self._regions_cache.keys())