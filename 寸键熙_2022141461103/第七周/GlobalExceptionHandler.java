package com.atc.alpha.track.exception;

import com.atc.alpha.track.dto.ApiResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.stream.Collectors;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    // 参数校验异常（@Valid失效时）
    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ApiResponse<Void> handleValidation(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
                .map(err -> err.getField() + ": " + err.getDefaultMessage())
                .collect(Collectors.joining("; "));
        log.warn("参数校验失败: {}", message);
        return ApiResponse.error(400, message);
    }

    // 业务异常（可恢复重试）
    @ExceptionHandler(RetryableException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ApiResponse<Void> handleRetryable(RetryableException e) {
        log.error("可恢复异常，触发重试机制: {}", e.getMessage());
        // 实际重试逻辑在调用方实现
        return ApiResponse.error(503, "服务暂时不可用，请稍后重试");
    }

    // 不可恢复异常
    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ApiResponse<Void> handleGeneric(Exception e) {
        log.error("系统不可恢复异常", e);
        return ApiResponse.error(500, "服务器内部错误");
    }
}