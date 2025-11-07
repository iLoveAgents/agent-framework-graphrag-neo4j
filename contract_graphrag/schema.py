"""Schema definitions for contract extraction using structured outputs."""

from enum import Enum

from pydantic import BaseModel, Field


class ContractType(str, Enum):
    """Valid contract types from CUAD dataset."""

    AFFILIATE_AGREEMENT = "Affiliate Agreement"
    AGENCY_AGREEMENT = "Agency Agreement"
    COLLABORATION_AGREEMENT = "Collaboration/Cooperation Agreement"
    CO_BRANDING_AGREEMENT = "Co-Branding Agreement"
    CONSULTING_AGREEMENT = "Consulting Agreement"
    DEVELOPMENT_AGREEMENT = "Development Agreement"
    DISTRIBUTOR_AGREEMENT = "Distributor Agreement"
    ENDORSEMENT_AGREEMENT = "Endorsement Agreement"
    FRANCHISE_AGREEMENT = "Franchise Agreement"
    HOSTING_AGREEMENT = "Hosting Agreement"
    IP_AGREEMENT = "IP Agreement"
    JOINT_VENTURE_AGREEMENT = "Joint Venture Agreement"
    LICENSE_AGREEMENT = "License Agreement"
    MAINTENANCE_AGREEMENT = "Maintenance Agreement"
    MANUFACTURING_AGREEMENT = "Manufacturing Agreement"
    MARKETING_AGREEMENT = "Marketing Agreement"
    NON_COMPETE_AGREEMENT = "Non-Compete/No-Solicit/Non-Disparagement Agreement"
    OUTSOURCING_AGREEMENT = "Outsourcing Agreement"
    PROMOTION_AGREEMENT = "Promotion Agreement"
    RESELLER_AGREEMENT = "Reseller Agreement"
    SERVICE_AGREEMENT = "Service Agreement"
    SPONSORSHIP_AGREEMENT = "Sponsorship Agreement"
    SUPPLY_AGREEMENT = "Supply Agreement"
    STRATEGIC_ALLIANCE_AGREEMENT = "Strategic Alliance Agreement"
    TRANSPORTATION_AGREEMENT = "Transportation Agreement"
    OTHER = "Other"


class ClauseType(str, Enum):
    """Valid clause types to extract from contracts."""

    COMPETITIVE_RESTRICTION_EXCEPTION = "Competitive Restriction Exception"
    NON_COMPETE = "Non-Compete"
    EXCLUSIVITY = "Exclusivity"
    NO_SOLICIT_CUSTOMERS = "No-Solicit Of Customers"
    NO_SOLICIT_EMPLOYEES = "No-Solicit Of Employees"
    NON_DISPARAGEMENT = "Non-Disparagement"
    TERMINATION_FOR_CONVENIENCE = "Termination For Convenience"
    ROFR_ROFO_ROFN = "Rofr/Rofo/Rofn"
    CHANGE_OF_CONTROL = "Change Of Control"
    ANTI_ASSIGNMENT = "Anti-Assignment"
    REVENUE_PROFIT_SHARING = "Revenue/Profit Sharing"
    PRICE_RESTRICTIONS = "Price Restrictions"
    MINIMUM_COMMITMENT = "Minimum Commitment"
    VOLUME_RESTRICTION = "Volume Restriction"
    IP_OWNERSHIP_ASSIGNMENT = "IP Ownership Assignment"
    JOINT_IP_OWNERSHIP = "Joint IP Ownership"
    LICENSE_GRANT = "License grant"
    NON_TRANSFERABLE_LICENSE = "Non-Transferable License"
    AFFILIATE_LICENSE_LICENSOR = "Affiliate License-Licensor"
    AFFILIATE_LICENSE_LICENSEE = "Affiliate License-Licensee"
    UNLIMITED_LICENSE = "Unlimited/All-You-Can-Eat-License"
    IRREVOCABLE_PERPETUAL_LICENSE = "Irrevocable Or Perpetual License"
    SOURCE_CODE_ESCROW = "Source Code Escrow"
    POST_TERMINATION_SERVICES = "Post-Termination Services"
    AUDIT_RIGHTS = "Audit Rights"
    UNCAPPED_LIABILITY = "Uncapped Liability"
    CAP_ON_LIABILITY = "Cap On Liability"
    LIQUIDATED_DAMAGES = "Liquidated Damages"
    WARRANTY_DURATION = "Warranty Duration"
    INSURANCE = "Insurance"
    COVENANT_NOT_TO_SUE = "Covenant Not To Sue"
    THIRD_PARTY_BENEFICIARY = "Third Party Beneficiary"


class Party(BaseModel):
    """A party to the contract."""

    role: str = Field(
        description="The role of the party (e.g., 'Vendor', 'Customer', 'Licensor', 'Licensee')"
    )
    name: str = Field(description="The legal name of the party")
    incorporation_country: str = Field(
        default="",
        description="Country where the party is incorporated (ISO 3166 country name). Use empty string if not found.",
    )
    incorporation_state: str = Field(
        default="",
        description="State/province where the party is incorporated. Use empty string if not found.",
    )


class GoverningLaw(BaseModel):
    """Governing law and jurisdiction information."""

    country: str = Field(
        default="",
        description="Country of governing law (ISO 3166 country name). Use empty string if not found.",
    )
    state: str = Field(
        default="", description="State/province of governing law. Use empty string if not found."
    )
    most_favored_country: str = Field(
        default="",
        description="Most favored country if multiple countries mentioned, otherwise same as country. Use empty string if not found.",
    )


class ContractClause(BaseModel):
    """A clause found in the contract."""

    clause_type: ClauseType = Field(
        description="Type of clause from the predefined ClauseType enum"
    )
    exists: bool = Field(description="Whether this clause type exists in the contract")
    excerpts: list[str] = Field(
        default_factory=list,
        description="Full text excerpts from the contract that support the existence of this clause. Extract complete paragraphs or relevant text passages.",
    )


class Agreement(BaseModel):
    """Complete contract/agreement information."""

    agreement_name: str = Field(
        default="",
        description="Name or title of the agreement as stated in the document. Use empty string if not found.",
    )
    agreement_type: ContractType = Field(
        description="Type of agreement from the predefined ContractType enum. Choose the most appropriate type."
    )
    agreement_date: str = Field(
        default="",
        description="Agreement/signing date (yyyy-mm-dd format if absolute date). Use empty string if not found.",
    )
    effective_date: str = Field(
        default="",
        description="Effective date of the agreement (yyyy-mm-dd format if absolute date). Use empty string if not found.",
    )
    expiration_date: str = Field(
        default="",
        description="Expiration date of the agreement (yyyy-mm-dd format if absolute date). Use empty string if not found.",
    )
    renewal_term: str = Field(
        default="", description="Terms for renewal of the agreement. Use empty string if not found."
    )
    Notice_period_to_Terminate_Renewal: str = Field(
        default="",
        description="Notice period required to terminate renewal. Use empty string if not found.",
    )
    parties: list[Party] = Field(
        default_factory=list, description="All parties involved in the agreement"
    )
    governing_law: GoverningLaw = Field(
        default_factory=GoverningLaw, description="Governing law and jurisdiction"
    )
    clauses: list[ContractClause] = Field(
        description="All clause types with their existence status and excerpts"
    )


class ContractExtraction(BaseModel):
    """Top-level structure for extracted contract information."""

    agreement: Agreement = Field(description="The extracted agreement/contract information")
