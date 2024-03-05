# To use the ZED in your application, you will need to create and open a Camera object.
# The API can be used with two different video inputs:
#   1. the ZED live video (Live mode)
#   2. video files recorded in SVO format with the ZED API (Playback mode)
import pyzed.sl as sl
import numpy    as np
import matplotlib.pyplot as plt
import cv2


if __name__ == '__main__':
    timestamp = None
    # To configure the camera, create a Camera object and specify your `InitParameters`.
    # Initial parameters let you adjust camera resolution, FPS, depth sensing parameters and more.
    # These parameters can only be set before opening the camera and cannot be changed while the camera is in use.

    # Create a ZED camera object
    zed = sl.Camera()

    # Set configuration parameters
    init_params                     = sl.InitParameters()
    init_params.camera_resolution   = sl.RESOLUTION.HD1080
    init_params.camera_fps          = 30
    init_params.depth_mode          = sl.DEPTH_MODE.PERFORMANCE  # Set the depth mode to performance (fastest)
    init_params.coordinate_units    = sl.UNIT.MILLIMETER  # Use millimeter units
    # ...
    # 完整的 InitParameters 参数可见: https://www.stereolabs.com/docs/api/structsl_1_1InitParameters.html

    # Once the initial configuration is done, open the camera.
    err = zed.open(init_params)
    if err != sl.ERROR_CODE.SUCCESS:
        exit()

    # 可以为每个镜头和分辨率检索 焦距、视场或立体校准等相机参数。
    # 这些值可在 CalibrationParameters（校准参数）中找到。可以使用 getCameraInformation() 访问它们。
    zed_serial = zed.get_camera_information().serial_number
    print("Hello! This is my serial number: {}".format(zed_serial))
    # IMU 等传感器的配置文件可见 Sensors API: https://www.stereolabs.com/docs/sensors/using-sensors

    # To capture an image and process it, you need to call the Camera::grab() function.
    # This function can take runtime parameters as well, but we leave them to default in this tutorial.
    image               = sl.Mat()
    depth               = sl.Mat()
    point               = sl.Mat()  # Depth Map: the value
    depth_view          = sl.Mat()  # Color rendering of the depth.
    #                                 Type: sl.MAT_TYPE.U8_C4
    #                                 Each pixel contains 4 unsigned char (B, G, R, A).
    runtime_parameters  = sl.RuntimeParameters()

    if zed.grab(runtime_parameters) == sl.ERROR_CODE.SUCCESS:
        # A new image is available if grab() returns ERROR_CODE.SUCCESS
        # grab() 方法会捕获当前时刻的所有的传感器信息, 即具有相同的时间戳
        # Note: Image timestamp is given in nanoseconds and Epoch format.
        # You can compare the timestamps between two grab():
        #   it should be close to the framerate time, if you don’t have any dropped frames.
        zed.retrieve_image(
            image,          # 用于获取图像帧
            sl.VIEW.LEFT    # 获得左相机图像
        )
        zed.retrieve_measure(depth, sl.MEASURE.DEPTH)           # Retrieve depth matrix.
        #                                                       # Depth is aligned on the left RGB image
        zed.retrieve_image(depth_view, sl.VIEW.DEPTH)           # gray-scale version of the depth map from camera/SVO
        # `VIEW.DEPTH` can be used to get a gray-scale version of the depth map,
        # but the actual depth values can be retrieved using `retrieve_measure()` .
        # VIEW 支持的宏列表: https://www.stereolabs.com/docs/api/python/classpyzed_1_1sl_1_1VIEW.html

        zed.retrieve_measure(point, sl.MEASURE.XYZRGBA)         # Retrieve colored point cloud

        timestamp = zed.get_timestamp(sl.TIME_REFERENCE.IMAGE)  # Get the image timestamp
        print("Image resolution: {0} x {1} || Image timestamp: {2}\n".format(
            image.get_width(),
            image.get_height(),
            timestamp.get_milliseconds()))

    # If grab() returns SUCCESS, a new image has been captured and is now available.
    # You can also check the status of grab() which tells you if there is an issue during capture.

    # 如果想要对通过相机获得的数据进行处理, 需要先转变其数据格式. e.g. <class 'numpy.ndarray'>
    # get_data() 会将 sl.Mat() 数据转换为 numpy 数据类型
    image_data = image.get_data()
    depth_data = depth.get_data()
    depth_imag = depth_view.get_data()  # 获得的灰度图版本的 深度图 按照图像的方式进行获取
    point_data = point.get_data()

    print(depth.get_pixel_bytes(), '\n',    # Returns the size of one pixel in bytes.
          depth.get_data_type(), '\n',      # Returns the format of the matrix.
          depth.get_infos(), '\n',          # Returns the information about the sl.Mat into a string.
          depth.get_step_bytes(), '\n',     # 数据简报:
          # n/a Ts 1709651329565919300 sl::Mat of size [1920,1080], with 1 channels of type float allocated on CPU (memory owned).
          )
    print(depth_data.shape)
    print(type(depth_data[0][0]))           # ZED SDK 中的深度图通常以 <class 'numpy.float32'> 数据类型存储。



    # 获取某点的深度
    x_value = 1000
    y_value = 600
    print("The depth of the {0} {1} is {2}".format(x_value,
                                                   y_value,
                                                   depth.get_value(x=x_value, y=y_value)  # 获取深度: (SUCCESS, nan)
                                                   )
          )
    # The depth of the 1000 600 is (SUCCESS, 709.8384399414062)

    # RGB LEFT_VIEW 可视化
    cv2.circle(image_data, (x_value, y_value), 5, (0, 0, 255), 1)
    cv2.imshow("LEFT View", image_data)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # 深度图 可视化
    cv2.imshow("Depth View", depth_imag)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # 保存矩阵到文本文件，使用numpy.savetxt，保留足够的小数位以保持精度
    # 可视化使用图: image_imag
    # 获取深度数据: image_data
    filename = f"{timestamp.get_milliseconds()}.txt"
    np.savetxt(filename, depth_data, fmt="%.8f")

    # Close the camera
    zed.close()
