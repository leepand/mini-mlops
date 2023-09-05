"""Prompt schema definition."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from string import Formatter
import pkg_resources
import os

from .base import (
    check_valid_template,
    DEFAULT_FORMATTER_MAPPING,
    _get_jinja2_variables_from_template,
)


class PromptTemplate:
    """A prompt template for a language model.

    A prompt template consists of a string template. It accepts a set of parameters
    from the user that can be used to generate a prompt for a language model.

    The template can be formatted using either f-strings (default) or jinja2 syntax.

    Example:

        .. code-block:: python

            from mlopskit.ext.prompts import PromptTemplate

            # Instantiation using from_template (recommended)
            prompt = PromptTemplate.from_template("Say {foo}")
            prompt.format(foo="bar")

            # Instantiation using initializer
            prompt = PromptTemplate(input_variables=["foo"], template="Say {foo}")
    """

    def __init__(
        self,
        input_variables: List[str],
        template: str,
        template_format: str = "jinja2",
        validate_template: bool = True,
        partial_variables: dict = {},
    ):
        self.partial_variables = partial_variables
        self.input_variables = input_variables

        """input_variables : A list of the names of the variables the prompt template expects."""
        self.template = template
        """The prompt template."""

        self.template_format = template_format
        """The format of the prompt template. Options are: 'f-string', 'jinja2'."""

        self.validate_template = validate_template
        """Whether or not to try validating the template."""

    @property
    def _prompt_type(self) -> str:
        """Return the prompt type key."""
        return "prompt"

    @property
    def lc_attributes(self) -> Dict[str, Any]:
        return {
            "template_format": self.template_format,
        }

    def format(self, **kwargs: Any) -> str:
        """Format the prompt with the inputs.

        Args:
            kwargs: Any arguments to be passed to the prompt template.

        Returns:
            A formatted string.

        Example:

            .. code-block:: python

                prompt.format(variable1="foo")
        """
        kwargs = self._merge_partial_and_user_variables(**kwargs)
        return DEFAULT_FORMATTER_MAPPING[self.template_format](self.template, **kwargs)

    def template_is_valid(cls, values: Dict) -> Dict:
        """Check that template and input variables are consistent."""
        if values["validate_template"]:
            all_inputs = values["input_variables"] + list(values["partial_variables"])
            check_valid_template(
                values["template"], values["template_format"], all_inputs
            )
        return values

    def _merge_partial_and_user_variables(self, **kwargs: Any) -> Dict[str, Any]:
        # Get partial params:
        partial_kwargs = {
            k: v if isinstance(v, str) else v()
            for k, v in self.partial_variables.items()
        }
        return {**partial_kwargs, **kwargs}

    @classmethod
    def from_file(
        cls, template_file: Union[str, Path], input_variables: List[str], **kwargs: Any
    ) -> PromptTemplate:
        """Load a prompt from a file.

        Args:
            template_file: The path to the file containing the prompt template.
            input_variables: A list of variable names the final prompt template
                will expect.

        Returns:
            The prompt loaded from the file.
        """
        with open(str(template_file), "r") as f:
            template = f.read()
        return cls(input_variables=input_variables, template=template, **kwargs)

    @classmethod
    def from_template(
        cls,
        template: str,
        *,
        template_format: str = "f-string",
        partial_variables: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> PromptTemplate:
        """Load a prompt template from a template.

        Args:
            template: The template to load.
            template_format: The format of the template. Use `jinja2` for jinja2,
                             and `f-string` or None for f-strings.
            partial_variables: A dictionary of variables that can be used to partially
                               fill in the template. For example, if the template is
                              `"{variable1} {variable2}"`, and `partial_variables` is
                              `{"variable1": "foo"}`, then the final prompt will be
                              `"foo {variable2}"`.

        Returns:
            The prompt template loaded from the template.
        """
        if template_format == "jinja2":
            # Get the variables for the template
            input_variables = _get_jinja2_variables_from_template(template)
        elif template_format == "f-string":
            input_variables = {
                v for _, v, _, _ in Formatter().parse(template) if v is not None
            }
        else:
            raise ValueError(f"Unsupported template format: {template_format}")

        _partial_variables = partial_variables or {}

        if _partial_variables:
            input_variables = {
                var for var in input_variables if var not in _partial_variables
            }

        return cls(
            input_variables=sorted(input_variables),
            template=template,
            template_format=template_format,
            partial_variables=_partial_variables,
            **kwargs,
        )


# For backwards compatibility.
Prompt = PromptTemplate

PACKAGE_NAME = "mlopskit"


def create_template(filename, input_variables, template_format="f-string", **kwargs):
    file_path = pkg_resources.resource_filename(
        PACKAGE_NAME, f"ext/templates/{filename}"
    )
    file_template = PromptTemplate.from_file(
        file_path, input_variables=input_variables, template_format=template_format
    )
    file_contents = file_template.format(**kwargs)

    # file_write_path = os.path.join(project_path, filename)
    return file_contents


def readfile(sh, filename):
    file_path = pkg_resources.resource_filename(
        PACKAGE_NAME, f"ext/templates/{filename}"
    )
    return sh.read(file_path)
