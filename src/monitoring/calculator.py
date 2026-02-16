"""
Cost calculator following SPEC-ENHANCE-004 FR-5.

Provides cost calculation functionality:
- Provider-specific pricing (Claude, ChatGPT, Gemini, Perplexity)
- Input/output token differentiation
- Cost estimation for budget planning
"""


from core.models import AgentType


class PricingConfig:
    """
    Pricing configuration for AI providers.

    Prices are in USD per 1M tokens (2026 rates from SPEC-ENHANCE-004).

    Attributes:
        custom_pricing: Optional custom pricing overrides
    """

    # Default pricing (USD/1M tokens) - class variable
    DEFAULT_PRICING: dict[AgentType, dict[str, float]] = {
        AgentType.CLAUDE: {"input": 3.00, "output": 15.00},
        AgentType.CHATGPT: {"input": 10.00, "output": 30.00},
        AgentType.GEMINI: {"input": 1.25, "output": 5.00},
        AgentType.PERPLEXITY: {"input": 1.00, "output": 1.00},
    }

    def __init__(
        self, custom_pricing: dict[AgentType, dict[str, float]] | None = None
    ) -> None:
        """
        Initialize pricing configuration.

        Args:
            custom_pricing: Optional custom pricing overrides
        """
        self.custom_pricing = custom_pricing

    def get_pricing(self, provider: AgentType, is_input: bool) -> float:
        """
        Get pricing for provider and token type.

        Args:
            provider: AI provider type
            is_input: True for input tokens, False for output tokens

        Returns:
            Price per 1M tokens in USD
        """
        # Check custom pricing first
        if self.custom_pricing and provider in self.custom_pricing:
            pricing = self.custom_pricing[provider]
            key = "input" if is_input else "output"
            return pricing.get(key, 0.0)

        # Use default pricing
        if provider in self.DEFAULT_PRICING:
            pricing = self.DEFAULT_PRICING[provider]
            key = "input" if is_input else "output"
            return pricing[key]

        # Unknown provider
        return 0.0


class CostCalculator:
    """
    Calculate AI costs from token usage.

    Responsibilities:
    - Calculate cost from token counts
    - Estimate costs for budget planning
    - Support custom pricing configurations

    Reference: SPEC-ENHANCE-004 FR-5
    """

    def __init__(self, pricing_config: PricingConfig | None = None) -> None:
        """
        Initialize cost calculator.

        Args:
            pricing_config: Custom pricing configuration (default: use SPEC pricing)
        """
        self.pricing_config = pricing_config or PricingConfig()

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        provider: AgentType,
    ) -> float:
        """
        Calculate cost from token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            provider: AI provider type

        Returns:
            Cost in USD
        """
        input_price = self.pricing_config.get_pricing(provider, is_input=True)
        output_price = self.pricing_config.get_pricing(provider, is_input=False)

        # Calculate cost (prices are per 1M tokens)
        input_cost = (input_tokens * input_price) / 1_000_000
        output_cost = (output_tokens * output_price) / 1_000_000

        return input_cost + output_cost

    def estimate_cost(
        self,
        tokens: int,
        provider: AgentType,
        is_input: bool = True,
    ) -> float:
        """
        Estimate cost for a given number of tokens.

        Args:
            tokens: Number of tokens
            provider: AI provider type
            is_input: True for input tokens, False for output tokens

        Returns:
            Estimated cost in USD
        """
        price = self.pricing_config.get_pricing(provider, is_input=is_input)
        return (tokens * price) / 1_000_000
