"""
Mutation resolvers for the GraphQL server.

This module implements GraphQL mutation resolvers for:
- generate_speech: Generates speech from text using TTS engines
- translate_text: Translates text using translation engines

Both mutations support synchronous and asynchronous execution modes.
"""

from typing import Union, TYPE_CHECKING

import strawberry

from server.graphql.types.outputs import TTSResult, TranslationResult, JobStatusEnum

if TYPE_CHECKING:
    from server.graphql.context import Context
    from server.graphql.types.inputs import TTSInput, TranslationInput


# =========================== Job Created Response Type =========================== #


@strawberry.type
class JobCreated:
    """Response when an asynchronous job is created."""

    job_id: str
    message: str
    status: JobStatusEnum


# =========================== Mutation Resolvers =========================== #


@strawberry.type
class Mutation:
    """
    GraphQL Mutation type with write operations.

    Provides mutations for:
    - TTS generation (synchronous and asynchronous)
    - Text translation (synchronous and asynchronous)
    """

    @strawberry.mutation
    async def generate_speech(
        self, input: "TTSInput", async_mode: bool = False, info: strawberry.Info = None
    ) -> Union[TTSResult, JobCreated]:
        """
        Generates speech from text using specified TTS engine.

        This mutation accepts TTS parameters and either:
        - Executes synchronously and returns TTSResult immediately
        - Creates an async job and returns JobCreated with job_id for tracking

        Process:
        1. Validate input parameters (engine, text_content/file_upload)
        2. Check async_mode flag
        3. If async: create job via JobManager, return JobCreated
        4. If sync: call TTSService.generate_speech(), return TTSResult

        Args:
            input: TTSInput with TTS parameters (engine, text_content, etc.)
            async_mode: If True, execute asynchronously and return job_id
            info: Strawberry info object containing context

        Returns:
            Union[TTSResult, JobCreated]: Result or job ID depending on async_mode

        Raises:
            Exception: If validation fails or processing errors occur

        Examples:
            Synchronous execution:
            ```graphql
            mutation {
              generateSpeech(
                input: {
                  textContent: "Hello world"
                  engine: ONLINE
                  chunkSize: 3500
                }
                asyncMode: false
              ) {
                ... on TTSResult {
                  success
                  message
                  outputFiles
                  metadata {
                    engineUsed
                    totalChunks
                  }
                }
              }
            }
            ```

            Asynchronous execution:
            ```graphql
            mutation {
              generateSpeech(
                input: {
                  textContent: "Long text..."
                  engine: G_CLOUD
                }
                asyncMode: true
              ) {
                ... on JobCreated {
                  jobId
                  message
                  status
                }
              }
            }
            ```
        """
        context: Context = info.context
        logger = context.logger

        logger.info(
            f"Mutation: generate_speech (async_mode={async_mode})",
            extra={
                "async_mode": async_mode,
                "engine": input.engine if hasattr(input, "engine") else "unknown",
            },
        )

        try:
            # Validate input parameters
            self._validate_tts_input(input, logger)

            # Get services from context
            tts_service = context.request.app.state.tts_service

            # Check if async_mode is true
            if async_mode:
                # Async execution: create job via JobManager
                logger.info("Creating async TTS job")

                job_manager = context.request.app.state.job_manager

                # Create job and start background execution
                job_id = await job_manager.create_job(
                    job_type="TTS",
                    service_func=lambda inp, progress_callback:
                    # Note: We need to handle async/sync conversion here
                    # The service function is async but executor expects sync
                    self._run_async_service(
                        tts_service.generate_speech, inp, progress_callback
                    ),
                    input_data=input,
                )

                logger.info(f"Created async TTS job with ID: {job_id}")

                # Return JobCreated response
                return JobCreated(
                    job_id=job_id,
                    message=f"TTS job created successfully. Use jobStatus query to track progress.",
                    status=JobStatusEnum.QUEUED,
                )

            else:
                # Synchronous execution: call TTSService.generate_speech()
                logger.info("Executing TTS synchronously")

                result = await tts_service.generate_speech(
                    input_data=input, progress_callback=None
                )

                logger.info(
                    f"TTS generation completed: {len(result.output_files)} files generated",
                    extra={
                        "success": result.success,
                        "output_files": len(result.output_files),
                    },
                )

                # Return TTSResult
                return result

        except ValueError as e:
            # Validation or processing error
            error_msg = f"TTS generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)

        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error during TTS generation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)

    @strawberry.mutation
    async def translate_text(
        self,
        input: "TranslationInput",
        async_mode: bool = False,
        info: strawberry.Info = None,
    ) -> Union[TranslationResult, JobCreated]:
        """
        Translates text using specified translation engine.

        This mutation accepts translation parameters and either:
        - Executes synchronously and returns TranslationResult immediately
        - Creates an async job and returns JobCreated with job_id for tracking

        Process:
        1. Validate input parameters (engine, text_content/file_upload, languages)
        2. Check async_mode flag
        3. If async: create job via JobManager, return JobCreated
        4. If sync: call TranslationService.translate_text(), return TranslationResult

        Args:
            input: TranslationInput with translation parameters
            async_mode: If True, execute asynchronously and return job_id
            info: Strawberry info object containing context

        Returns:
            Union[TranslationResult, JobCreated]: Result or job ID depending on async_mode

        Raises:
            Exception: If validation fails or processing errors occur

        Examples:
            Synchronous execution:
            ```graphql
            mutation {
              translateText(
                input: {
                  textContent: "Hello world"
                  engine: OPENAI
                  sourceLanguage: "en"
                  targetLanguage: "cs"
                  openaiApiKey: "sk-..."
                }
                asyncMode: false
              ) {
                ... on TranslationResult {
                  success
                  message
                  outputFile
                  metadata {
                    engineUsed
                    sourceLanguage
                    targetLanguage
                  }
                }
              }
            }
            ```

            Asynchronous execution:
            ```graphql
            mutation {
              translateText(
                input: {
                  textContent: "Long text..."
                  engine: GEMINI
                  sourceLanguage: "en"
                  targetLanguage: "de"
                }
                asyncMode: true
              ) {
                ... on JobCreated {
                  jobId
                  message
                  status
                }
              }
            }
            ```
        """
        context: Context = info.context
        logger = context.logger

        logger.info(
            f"Mutation: translate_text (async_mode={async_mode})",
            extra={
                "async_mode": async_mode,
                "engine": input.engine if hasattr(input, "engine") else "unknown",
            },
        )

        try:
            # Validate input parameters
            self._validate_translation_input(input, logger)

            # Get services from context
            translation_service = context.request.app.state.translation_service

            # Check if async_mode is true
            if async_mode:
                # Async execution: create job via JobManager
                logger.info("Creating async translation job")

                job_manager = context.request.app.state.job_manager

                # Create job and start background execution
                job_id = await job_manager.create_job(
                    job_type="TRANSLATION",
                    service_func=lambda inp, progress_callback:
                    # Note: We need to handle async/sync conversion here
                    # The service function is async but executor expects sync
                    self._run_async_service(
                        translation_service.translate_text, inp, progress_callback
                    ),
                    input_data=input,
                )

                logger.info(f"Created async translation job with ID: {job_id}")

                # Return JobCreated response
                return JobCreated(
                    job_id=job_id,
                    message=f"Translation job created successfully. Use jobStatus query to track progress.",
                    status=JobStatusEnum.QUEUED,
                )

            else:
                # Synchronous execution: call TranslationService.translate_text()
                logger.info("Executing translation synchronously")

                result = await translation_service.translate_text(
                    input_data=input, progress_callback=None
                )

                logger.info(
                    f"Translation completed successfully",
                    extra={
                        "success": result.success,
                        "output_file": result.output_file,
                    },
                )

                # Return TranslationResult
                return result

        except ValueError as e:
            # Validation or processing error
            error_msg = f"Translation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)

        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error during translation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)

    # =========================== Helper Methods =========================== #

    def _validate_tts_input(self, input: "TTSInput", logger) -> None:
        """
        Validate TTS input parameters.

        Checks that required parameters are provided:
        - Either text_content or file_upload must be present
        - Engine must be specified

        Args:
            input: TTSInput object to validate
            logger: Logger instance for validation messages

        Raises:
            ValueError: If validation fails
        """
        # Check if we have input source
        has_upload = hasattr(input, "file_upload") and input.file_upload is not None
        has_text = hasattr(input, "text_content") and input.text_content

        if not has_upload and not has_text:
            error_msg = "Either text_content or file_upload must be provided"
            logger.warning(f"TTS validation failed: {error_msg}")
            raise ValueError(error_msg)

        # Check if engine is specified
        if not hasattr(input, "engine") or not input.engine:
            error_msg = "TTS engine must be specified"
            logger.warning(f"TTS validation failed: {error_msg}")
            raise ValueError(error_msg)

        logger.debug("TTS input validation passed")

    def _validate_translation_input(self, input: "TranslationInput", logger) -> None:
        """
        Validate translation input parameters.

        Checks that required parameters are provided:
        - Either text_content or file_upload must be present
        - Engine must be specified
        - Source and target languages must be specified

        Args:
            input: TranslationInput object to validate
            logger: Logger instance for validation messages

        Raises:
            ValueError: If validation fails
        """
        # Check if we have input source
        has_upload = hasattr(input, "file_upload") and input.file_upload is not None
        has_text = hasattr(input, "text_content") and input.text_content

        if not has_upload and not has_text:
            error_msg = "Either text_content or file_upload must be provided"
            logger.warning(f"Translation validation failed: {error_msg}")
            raise ValueError(error_msg)

        # Check if engine is specified
        if not hasattr(input, "engine") or not input.engine:
            error_msg = "Translation engine must be specified"
            logger.warning(f"Translation validation failed: {error_msg}")
            raise ValueError(error_msg)

        # Check if source language is specified
        if not hasattr(input, "source_language") or not input.source_language:
            error_msg = "Source language must be specified"
            logger.warning(f"Translation validation failed: {error_msg}")
            raise ValueError(error_msg)

        # Check if target language is specified
        if not hasattr(input, "target_language") or not input.target_language:
            error_msg = "Target language must be specified"
            logger.warning(f"Translation validation failed: {error_msg}")
            raise ValueError(error_msg)

        logger.debug("Translation input validation passed")

    def _run_async_service(self, service_func, input_data, progress_callback):
        """
        Helper to run async service function in sync context.

        The JobManager executor expects synchronous functions, but our
        service methods are async. This helper bridges the gap.

        Args:
            service_func: Async service function to execute
            input_data: Input parameters for the service
            progress_callback: Progress callback function

        Returns:
            Result from the service function
        """
        import asyncio

        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run the async function
        return loop.run_until_complete(service_func(input_data, progress_callback))
