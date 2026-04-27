import { gql } from "@apollo/client";

export const AVAILABLE_ENGINES_QUERY = gql`
  query AvailableEngines {
    availableEngines {
      ttsEngines {
        name
        description
        requiredParameters {
          name
          label
          fieldType
          choices
          accept
          defaultValue
          helpText
          required
        }
        optionalParameters {
          name
          label
          fieldType
          choices
          accept
          defaultValue
          helpText
          required
        }
      }
      translationEngines {
        name
        description
        requiredParameters {
          name
          label
          fieldType
          choices
          accept
          defaultValue
          helpText
          required
        }
        optionalParameters {
          name
          label
          fieldType
          choices
          accept
          defaultValue
          helpText
          required
        }
      }
    }
  }
`;

export const JOB_STATUS_QUERY = gql`
  query JobStatus($jobId: String!) {
    jobStatus(jobId: $jobId) {
      jobId
      status
      progress {
        percentage
        currentChunk
        totalChunks
        stage
        estimatedTimeRemaining
      }
      result {
        ... on TTSResultWithFile {
          success
          message
          outputFiles
          metadata {
            engineUsed
            totalChunks
            totalDurationSeconds
            outputDirectory
          }
          fileDownload {
            fileId
            filename
            downloadUrl
            contentType
            sizeBytes
          }
        }
        ... on TranslationResultWithFile {
          success
          message
          outputFile
          metadata {
            engineUsed
            sourceLanguage
            targetLanguage
            totalChunks
            outputDirectory
          }
          fileDownload {
            fileId
            filename
            downloadUrl
            contentType
            sizeBytes
          }
        }
      }
      error
    }
  }
`;
